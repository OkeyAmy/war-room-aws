import asyncio
from playwright import async_api
from playwright.async_api import expect

async def run_test():
    pw = None
    browser = None
    context = None

    try:
        # Start a Playwright session in asynchronous mode
        pw = await async_api.async_playwright().start()

        # Launch a Chromium browser in headless mode with custom arguments
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--window-size=1280,720",         # Set the browser window size
                "--disable-dev-shm-usage",        # Avoid using /dev/shm which can cause issues in containers
                "--ipc=host",                     # Use host-level IPC for better stability
                "--single-process"                # Run the browser in a single process mode
            ],
        )

        # Create a new browser context (like an incognito window)
        context = await browser.new_context()
        context.set_default_timeout(5000)

        # Open a new page in the browser context
        page = await context.new_page()

        # Interact with the page elements to simulate user flow
        # -> Navigate to http://localhost:3000
        await page.goto("http://localhost:3000", wait_until="commit", timeout=10000)
        
        # -> Input 'Severe coastal flooding with power outages' into the crisis description textarea (index 2), then wait briefly for the UI to update so additional interactive elements (like the Assemble Team button) may appear.
        frame = context.pages[-1]
        # Input text
        elem = frame.locator('xpath=/html/body/div[2]/div/form/div/textarea').nth(0)
        await page.wait_for_timeout(3000); await elem.fill('Severe coastal flooding with power outages')
        
        # -> Click the 'Assemble Team' button (index 76) to create/start the session, then wait for the war room to load.
        frame = context.pages[-1]
        # Click element
        elem = frame.locator('xpath=/html/body/div[2]/div/form/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        
        # -> Click the 'Assemble Team' button (index 302) to start the session, wait for the war room to load (allow an initial 20s wait), then extract the page content and verify that the 'Crisis Feed' is visible and at least one feed item shows a timestamp, a source/agent name, and message text.
        frame = context.pages[-1]
        # Click element
        elem = frame.locator('xpath=/html/body/div[2]/div/form/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        
        # -> Click the 'Assemble Team' button (index 412), wait 20 seconds for the war room to assemble, then extract the page content and check for 'Crisis Feed' and the first feed item's timestamp, source/agent name, and message text.
        frame = context.pages[-1]
        # Click element
        elem = frame.locator('xpath=/html/body/div[2]/div/form/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        
        # -> Click the Assemble Team button (index 526), wait up to 20s for the war room to load, then extract page content to verify the presence of 'Crisis Feed' and the first feed item's timestamp, source/agent name, and message text.
        frame = context.pages[-1]
        # Click element
        elem = frame.locator('xpath=/html/body/div[2]/div/form/button').nth(0)
        await page.wait_for_timeout(3000); await elem.click(timeout=5000)
        
        # --> Assertions to verify final state
        frame = context.pages[-1]
        await expect(frame.locator('text=Assembling').first).to_be_visible(timeout=3000)
        await expect(frame.locator('text=Crisis Feed').first).to_be_visible(timeout=3000)
        await expect(frame.locator('xpath=//section[(contains(@aria-label,"Crisis Feed") or contains(@class,"crisis-feed") or contains(@data-testid,"crisis-feed"))]//div[contains(@class,"feed-item")][1]//time').first).to_be_visible(timeout=3000)
        await expect(frame.locator('xpath=//section[(contains(@aria-label,"Crisis Feed") or contains(@class,"crisis-feed") or contains(@data-testid,"crisis-feed"))]//div[contains(@class,"feed-item")][1]//span[contains(@class,"agent") or contains(@class,"source") or contains(@class,"agent-name")]').first).to_be_visible(timeout=3000)
        await expect(frame.locator('xpath=//section[(contains(@aria-label,"Crisis Feed") or contains(@class,"crisis-feed") or contains(@data-testid,"crisis-feed"))]//div[contains(@class,"feed-item")][1]//p[contains(@class,"message") or contains(@class,"feed-message") or contains(@class,"message-text")]').first).to_be_visible(timeout=3000)
        await asyncio.sleep(5)

    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()

asyncio.run(run_test())
    