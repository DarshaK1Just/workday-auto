#!/usr/bin/env python3
"""
Dynamic Job Application Progress Extractor
Adapts to any job application form structure without hardcoded selectors
"""

import asyncio
import re
from typing import Dict, List, Optional, Any, Tuple
from playwright.async_api import async_playwright, Page, Browser, ElementHandle




class DynamicJobProgressExtractor:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def launch_browser(self, headless: bool = False) -> None:
        """Launch browser and create a new page"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=headless)
        self.page = await self.browser.new_page()

    async def find_progress_container(self, page: Page) -> Optional[ElementHandle]:
        """Dynamically find progress container using multiple strategies"""
        # Strategy 1: Look for common progress indicators
        progress_indicators = [
            '[aria-label*="progress" i]',
            '[aria-label*="step" i]',
            '[class*="progress" i]',
            '[class*="step" i]',
            '[data-automation-id*="progress" i]',
            '[data-testid*="progress" i]',
            'ol[class*="progress" i]',
            'ul[class*="progress" i]',
            'div[class*="stepper" i]',
            'nav[class*="step" i]'
        ]
        
        for selector in progress_indicators:
            try:
                container = await page.query_selector(selector)
                if container:
                    # Verify it contains step-like elements
                    steps = await container.query_selector_all('li, div[class*="step"], div[data-automation-id*="step"]')
                    if len(steps) > 1:  # Must have multiple steps
                        return container
            except:
                continue
        
        # Strategy 2: Look for elements with step-related data attributes
        step_elements = await page.query_selector_all('[data-automation-id*="step" i], [class*="step" i]')
        if len(step_elements) > 1:
            # Find common parent
            parent = await self.find_common_parent(step_elements)
            if parent:
                return parent
        
        return None

    async def find_common_parent(self, elements: List[ElementHandle]) -> Optional[ElementHandle]:
        """Find the common parent element of multiple elements"""
        if not elements:
            return None
        
        try:
            # Get parent of first element
            current_parent = await elements[0].query_selector('..')
            
            # Check if all elements share this parent
            for element in elements[1:]:
                element_parent = await element.query_selector('..')
                if not current_parent or not element_parent:
                    return None
                
                current_parent_html = await current_parent.inner_html()
                element_parent_html = await element_parent.inner_html()
                
                if current_parent_html != element_parent_html:
                    # Try going one level up
                    current_parent = await current_parent.query_selector('..')
                    if not current_parent:
                        return None
            
            return current_parent
        except:
            return None

    async def extract_step_elements(self, container: ElementHandle) -> List[ElementHandle]:
        """Extract all step elements from container"""
        # Try different step element patterns
        step_patterns = [
            'li',
            'div[class*="step"]',
            'div[data-automation-id*="step"]',
            'div[aria-label*="step"]',
            '[class*="step"]',
            'div[class*="item"]',
            'span[class*="step"]'
        ]
        
        for pattern in step_patterns:
            steps = await container.query_selector_all(pattern)
            if len(steps) > 1:
                return steps
        
        # Fallback: get direct children
        children = await container.query_selector_all('> *')
        return children if len(children) > 1 else []

    async def analyze_step_element(self, step_element: ElementHandle, index: int) -> Dict[str, Any]:
        """Analyze individual step element to extract information"""
        step_info = {
            'step_number': index + 1,
            'step_name': f'Step {index + 1}',
            'status': 'unknown',
            'is_active': False,
            'is_completed': False,
            'is_inactive': True,
            'progress_text': '',
            'raw_text': ''
        }
        
        try:
            # Get all text content
            all_text = await step_element.text_content()
            step_info['raw_text'] = all_text.strip() if all_text else ''
            
            # Analyze element attributes
            await self.analyze_element_attributes(step_element, step_info)
            
            # Extract step name from text content
            await self.extract_step_name_dynamic(step_element, step_info, index)
            
            # Determine status from various indicators
            await self.determine_step_status(step_element, step_info)
            
            # Extract progress information
            await self.extract_progress_info_dynamic(step_element, step_info)
            
        except Exception as e:
            print(f"Error analyzing step {index + 1}: {e}")
        
        return step_info

    async def analyze_element_attributes(self, element: ElementHandle, step_info: Dict[str, Any]) -> None:
        """Analyze element attributes for status indicators"""
        try:
            # Get all attributes
            attributes = await element.evaluate('el => Array.from(el.attributes).map(attr => [attr.name, attr.value])')
            
            for attr_name, attr_value in attributes:
                attr_lower = f"{attr_name}={attr_value}".lower()
                
                # Status indicators in attributes
                if any(word in attr_lower for word in ['completed', 'done', 'finished', 'success']):
                    step_info['status'] = 'completed'
                    step_info['is_completed'] = True
                    step_info['is_inactive'] = False
                elif any(word in attr_lower for word in ['active', 'current', 'selected', 'in-progress']):
                    step_info['status'] = 'active'
                    step_info['is_active'] = True
                    step_info['is_inactive'] = False
                elif any(word in attr_lower for word in ['inactive', 'disabled', 'pending', 'future']):
                    step_info['status'] = 'inactive'
        except:
            pass

    async def extract_step_name_dynamic(self, element: ElementHandle, step_info: Dict[str, Any], index: int) -> None:
        """Dynamically extract step name from various possible locations"""
        try:
            # Strategy 1: Look for text in child elements (labels, spans, divs)
            text_elements = await element.query_selector_all('label, span, div, p, h1, h2, h3, h4, h5, h6')
            
            for text_elem in text_elements:
                text = await text_elem.text_content()
                if text and len(text.strip()) > 0:
                    text = text.strip()
                    # Skip progress indicators like "step 1 of 4"
                    if not re.search(r'step\s+\d+\s+of\s+\d+', text, re.IGNORECASE):
                        if not re.search(r'^\d+\s*$', text):  # Skip pure numbers
                            if len(text) > 2 and len(text) < 50:  # Reasonable length
                                step_info['step_name'] = text
                                return
            
            # Strategy 2: Extract from aria-label or title
            aria_label = await element.get_attribute('aria-label')
            if aria_label and len(aria_label.strip()) > 2:
                step_info['step_name'] = aria_label.strip()
                return
            
            title = await element.get_attribute('title')
            if title and len(title.strip()) > 2:
                step_info['step_name'] = title.strip()
                return
            
            # Strategy 3: Parse from raw text
            raw_text = step_info['raw_text']
            if raw_text:
                # Try to extract meaningful text (not just numbers or progress indicators)
                lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
                for line in lines:
                    if not re.search(r'step\s+\d+\s+of\s+\d+', line, re.IGNORECASE):
                        if not re.search(r'^\d+\s*$', line):
                            if len(line) > 2 and len(line) < 50:
                                step_info['step_name'] = line
                                return
        
        except Exception as e:
            print(f"Error extracting step name: {e}")

    async def determine_step_status(self, element: ElementHandle, step_info: Dict[str, Any]) -> None:
        """Determine step status from visual and textual cues"""
        try:
            # If already determined from attributes, use that
            if step_info['status'] != 'unknown':
                return
            
            # Check for visual indicators (icons, colors, etc.)
            await self.check_visual_indicators(element, step_info)
            
            # Check text content for status keywords
            text_content = step_info['raw_text'].lower()
            
            if any(word in text_content for word in ['completed', 'done', 'finished', 'complete']):
                step_info['status'] = 'completed'
                step_info['is_completed'] = True
                step_info['is_inactive'] = False
            elif any(word in text_content for word in ['current', 'active', 'in progress', 'processing']):
                step_info['status'] = 'active'
                step_info['is_active'] = True
                step_info['is_inactive'] = False
            elif any(word in text_content for word in ['pending', 'waiting', 'next', 'upcoming']):
                step_info['status'] = 'inactive'
        
        except Exception as e:
            print(f"Error determining status: {e}")

    async def check_visual_indicators(self, element: ElementHandle, step_info: Dict[str, Any]) -> None:
        """Check for visual status indicators like checkmarks, colors, etc."""
        try:
            # Look for checkmark icons or success indicators
            checkmarks = await element.query_selector_all('svg, i, span[class*="check"], [class*="success"], [class*="complete"]')
            if checkmarks:
                step_info['status'] = 'completed'
                step_info['is_completed'] = True
                step_info['is_inactive'] = False
                return
            
            # Look for active/current indicators
            active_indicators = await element.query_selector_all('[class*="active"], [class*="current"], [class*="selected"]')
            if active_indicators:
                step_info['status'] = 'active'
                step_info['is_active'] = True
                step_info['is_inactive'] = False
                return
            
        except:
            pass

    async def extract_progress_info_dynamic(self, element: ElementHandle, step_info: Dict[str, Any]) -> None:
        """Extract progress information from text patterns"""
        try:
            text = step_info['raw_text']
            
            # Look for patterns like "step X of Y" or "X/Y"
            step_match = re.search(r'step\s+(\d+)\s+of\s+(\d+)', text, re.IGNORECASE)
            if step_match:
                step_info['step_number'] = int(step_match.group(1))
                step_info['progress_text'] = step_match.group(0)
                return
            
            fraction_match = re.search(r'(\d+)\s*/\s*(\d+)', text)
            if fraction_match:
                step_info['step_number'] = int(fraction_match.group(1))
                step_info['progress_text'] = fraction_match.group(0)
                return
                
        except:
            pass

    async def extract_progress_info(self, page: Optional[Page] = None) -> Dict[str, Any]:
        """Main extraction method"""
        if page is None:
            page = self.page
            
        if not page:
            return {"error": "No page available"}

        try:
            print("🔍 Searching for progress container...")
            
            # Find progress container dynamically
            container = await self.find_progress_container(page)
            if not container:
                return {"error": "Could not find progress container"}
            
            print("✅ Found progress container")
            
            # Extract step elements
            step_elements = await self.extract_step_elements(container)
            if not step_elements:
                return {"error": "No step elements found"}
            
            print(f"📊 Found {len(step_elements)} steps")
            
            # Analyze each step
            steps = []
            for i, step_element in enumerate(step_elements):
                step_info = await self.analyze_step_element(step_element, i)
                steps.append(step_info)
            
            # Calculate summary
            current_step = next((step for step in steps if step['is_active']), None)
            completed_steps = [step for step in steps if step['is_completed']]
            
            return {
                'total_steps': len(steps),
                'current_step': current_step['step_number'] if current_step else None,
                'completed_steps': len(completed_steps),
                'steps': steps,
                'current_step_name': current_step['step_name'] if current_step else None
            }
            
        except Exception as error:
            return {"error": f"Extraction failed: {str(error)}"}

    def print_progress_summary(self, progress_info: Dict[str, Any]) -> None:
        """Print formatted progress summary"""
        if "error" in progress_info:
            print(f"❌ Error: {progress_info['error']}")
            return
        
        print("\n🎯 JOB APPLICATION PROGRESS")
        print("=" * 50)
        print(f"📊 Total Steps: {progress_info['total_steps']}")
        print(f"✅ Completed: {progress_info['completed_steps']}")
        print(f"🔄 Current: {progress_info['current_step_name'] or 'None'}")
        print()
        
        print("📋 STEP DETAILS:")
        print("-" * 50)
        
        for step in progress_info['steps']:
            status_icons = {'completed': '✅', 'active': '🔄', 'inactive': '⏳', 'unknown': '❓'}
            status_colors = {'completed': '\033[32m', 'active': '\033[33m', 'inactive': '\033[37m', 'unknown': '\033[37m'}
            
            icon = status_icons.get(step['status'], '❓')
            color = status_colors.get(step['status'], '\033[37m')
            
            print(f"{icon} {color}Step {step['step_number']}: {step['step_name']}\033[0m")
            print(f"   Status: {step['status'].upper()}")
            if step['progress_text']:
                print(f"   Progress: {step['progress_text']}")
            print()

    async def run_extraction(self, url: Optional[str] = None) -> Dict[str, Any]:
        """Run complete extraction process"""
        if not self.page:
            await self.launch_browser()
        
        try:
            if url:
                print(f"🚀 Navigating to: {url}")
                await self.page.goto(url, wait_until='networkidle')
                await asyncio.sleep(2)  # Wait for dynamic content
            else:
                print("🔍 Please navigate to the job application page...")
                print("⏳ Press Enter when ready to extract...")
                input()
            
            progress_info = await self.extract_progress_info()
            self.print_progress_summary(progress_info)
            return progress_info
            
        except Exception as e:
            error_info = {"error": f"Execution failed: {str(e)}"}
            self.print_progress_summary(error_info)
            return error_info

    async def close(self) -> None:
        """Close browser"""
        if self.browser:
            await self.browser.close()


# Simple usage functions
async def extract_progress(url: Optional[str] = None, headless: bool = False) -> Dict[str, Any]:
    """Simple function to extract progress"""
    extractor = DynamicJobProgressExtractor()
    try:
        await extractor.launch_browser(headless=headless)
        return await extractor.run_extraction(url)
    finally:
        await extractor.close()


async def main():
    """Main execution"""
    extractor = DynamicJobProgressExtractor()
    
    try:
        await extractor.launch_browser(headless=False)
        
        print("🎯 Dynamic Job Progress Extractor")
        print("Navigate to any job application page and press Enter...")
        
        progress = await extractor.run_extraction("https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite/job/Senior-DevOps-Engineer_JR1997710/apply/applyManually")
        
        print("\n🔍 Browser kept open for inspection.")
        print("Press Ctrl+C to exit...")
        
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n👋 Closing...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await extractor.close()


if __name__ == "__main__":
    asyncio.run(main())