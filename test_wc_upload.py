"""
Playwright test for W&C Excel Upload workflow
Tests the complete flow: login -> navigate -> upload -> verify
"""

import asyncio
from playwright.async_api import async_playwright
import os

# Test credentials
EMAIL = "adi@imaiconsultants.com"
PASSWORD = "Admin123!"
BASE_URL = "http://localhost:8501"


async def test_wc_upload_workflow():
    """Test the W&C upload workflow end-to-end"""

    async with async_playwright() as p:
        # Launch browser (headless=False to see what's happening)
        browser = await p.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context()
        page = await context.new_page()

        print("\n" + "="*60)
        print("W&C Upload Workflow Test")
        print("="*60)

        try:
            # Step 1: Navigate to app
            print("\n[1] Navigating to app...")
            await page.goto(BASE_URL)
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)

            # Step 2: Login
            print("[2] Logging in...")

            # Wait for email input and fill
            email_input = page.locator('input[type="text"]').first
            await email_input.wait_for(timeout=10000)
            await email_input.fill(EMAIL)
            await asyncio.sleep(0.5)

            # Fill password
            password_input = page.locator('input[type="password"]').first
            await password_input.fill(PASSWORD)
            await asyncio.sleep(0.5)

            # Press Enter to submit (more reliable than clicking)
            await password_input.press("Enter")

            # Wait for page to change (login complete)
            print("   Waiting for login to complete...")
            await asyncio.sleep(5)

            # Check if we're still on login page
            page_content = await page.content()
            if "Sign In" in page_content and "Email Address" in page_content:
                # Still on login page - try clicking the button
                print("   Still on login page, clicking Sign In button...")
                login_btn = page.locator('button:has-text("Sign In")')
                await login_btn.click()
                await asyncio.sleep(5)

            # Take screenshot to see current state
            await page.screenshot(path="test_screenshots/after_login.png")
            print("   Screenshot: test_screenshots/after_login.png")

            # Wait for dashboard to load (look for sidebar or navigation)
            try:
                await page.wait_for_selector('[data-testid="stSidebar"]', timeout=15000)
                print("   Dashboard loaded!")
            except:
                print("   Sidebar not found, checking page state...")
                await page.screenshot(path="test_screenshots/login_state.png")

            # Step 3: Navigate to W&C Admin page via URL
            print("[3] Navigating to W&C Admin page...")

            # First try clicking in sidebar
            sidebar = page.locator('[data-testid="stSidebar"]')
            if await sidebar.count() > 0:
                # Look for W&C link in sidebar
                wc_options = [
                    'text=W&C Admin',
                    'text=Wins & Challenges',
                    '[data-testid="stSidebarNavLink"]:has-text("W&C")',
                    'button:has-text("W&C")',
                ]

                found = False
                for selector in wc_options:
                    link = page.locator(selector).first
                    if await link.count() > 0:
                        try:
                            await link.click()
                            found = True
                            print(f"   Clicked: {selector}")
                            break
                        except:
                            continue

                if not found:
                    # Try expanding Admin section first
                    admin_expander = page.locator('text=Admin').first
                    if await admin_expander.count() > 0:
                        await admin_expander.click()
                        await asyncio.sleep(1)

                        # Now try W&C link again
                        for selector in wc_options:
                            link = page.locator(selector).first
                            if await link.count() > 0:
                                try:
                                    await link.click()
                                    found = True
                                    print(f"   Clicked after expand: {selector}")
                                    break
                                except:
                                    continue

            await asyncio.sleep(3)
            await page.screenshot(path="test_screenshots/wc_page.png")

            # Check if we're on W&C page
            page_content = await page.content()
            if "Manage Wins" in page_content or "W&C" in page_content or "Upload W&C" in page_content:
                print("   On W&C Admin page!")
            else:
                print("   May not be on W&C page. Checking sidebar...")

            # Step 4: Look for the key UI elements
            print("[4] Checking UI elements...")

            # Look for company selector
            company_selector = page.locator('text=Select Company')
            if await company_selector.count() > 0:
                print("   Company selector: FOUND")
            else:
                print("   Company selector: NOT FOUND")

            # Look for period selector
            period_selector = page.locator('text=Select Period')
            if await period_selector.count() > 0:
                print("   Period selector: FOUND")
            else:
                print("   Period selector: NOT FOUND")

            # Look for file uploader
            file_uploader = page.locator('[data-testid="stFileUploader"]')
            if await file_uploader.count() > 0:
                print("   File uploader: FOUND")
            else:
                print("   File uploader: NOT FOUND")

            # Look for download button in sidebar
            download_btn = page.locator('button:has-text("Download")')
            if await download_btn.count() > 0:
                print("   Download template button: FOUND")
            else:
                print("   Download template button: NOT FOUND")

            # Step 5: Try uploading the test template
            print("[5] Attempting file upload...")
            template_path = os.path.abspath("bpc_upload_template/BPC2_WC_Upload_Template.xlsx")

            if os.path.exists(template_path):
                file_input = page.locator('input[type="file"]')
                if await file_input.count() > 0:
                    await file_input.set_input_files(template_path)
                    print(f"   Uploaded: {template_path}")
                    await asyncio.sleep(3)

                    await page.screenshot(path="test_screenshots/after_upload.png")
                    print("   Screenshot: test_screenshots/after_upload.png")

                    # Look for preview tabs
                    wins_tab = page.locator('button:has-text("Wins")')
                    if await wins_tab.count() > 0:
                        print("   Preview tabs: FOUND")

                    # Look for Upload as Draft button
                    upload_btn = page.locator('button:has-text("Upload as Draft")')
                    if await upload_btn.count() > 0:
                        print("   'Upload as Draft' button: FOUND")
                else:
                    print("   File input not found on page")
            else:
                print(f"   Template not found: {template_path}")

            # Final screenshot
            await page.screenshot(path="test_screenshots/final_state.png")
            print("\n[6] Test completed!")
            print("   Final screenshot: test_screenshots/final_state.png")

            # Keep browser open briefly
            print("\n" + "="*60)
            print("Browser will close in 8 seconds...")
            print("="*60)
            await asyncio.sleep(8)

        except Exception as e:
            print(f"\n[ERROR] Test failed: {str(e)}")
            await page.screenshot(path="test_screenshots/error.png")
            print("   Error screenshot: test_screenshots/error.png")
            raise
        finally:
            await browser.close()


if __name__ == "__main__":
    # Create screenshots directory
    os.makedirs("test_screenshots", exist_ok=True)

    # Run the test
    asyncio.run(test_wc_upload_workflow())
