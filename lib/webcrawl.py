from playwright.sync_api import sync_playwright
import time

PAGE_URL = "https://my.hiredly.com/about-us"
CMS_URL = "https://cms.hiredly.com"
MAX_RETRIES = 3
RETRY_DELAY = 3  # seconds

def run_check():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        cms_requests_found = False
        cms_cors_errors = False
        cms_responses = []

        # 1) Listen for CMS-related CORS console errors
        def on_console(msg):
            nonlocal cms_cors_errors
            if "has been blocked by CORS policy" in msg.text and CMS_URL in msg.text:
                print("CMS CORS Error:", msg.text)
                cms_cors_errors = True
        page.on("console", on_console)

        # 2) Listen for CMS responses
        def on_response(response):
            nonlocal cms_requests_found
            url = response.url
            if CMS_URL in url:
                cms_requests_found = True
                aca_origin = response.headers.get("access-control-allow-origin")
                status = response.status
                print(f" CMS Response: {url}")
                print(f" Status: {status}")
                print(f" ACAO: {aca_origin}")
                cms_responses.append({
                    'url': url,
                    'status': status,
                    'acao': aca_origin
                })
        page.on("response", on_response)

        # 3) Try page.goto with retries
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                print(f"Attempt {attempt}: Navigating to {PAGE_URL}")
                page.goto(PAGE_URL, timeout=30000, wait_until="domcontentloaded")
                page.wait_for_timeout(5000)  # allow time for network/console
                break
            except Exception as e:
                print(f"Page load error (attempt {attempt}): {e}")
                if attempt < MAX_RETRIES:
                    print(f"Retrying in {RETRY_DELAY}s...")
                    time.sleep(RETRY_DELAY)
                else:
                    print("RESULT: FAILED - Page failed to load after retries")
                    browser.close()
                    return

        # 4) Evaluate outcome
        if not cms_requests_found:
            print("RESULT: FAILED - No CMS requests detected")
        elif cms_cors_errors:
            print("RESULT: FAILED - CMS CORS errors detected")
        elif any(resp['status'] >= 400 for resp in cms_responses):
            print("RESULT: FAILED - CMS returned error status codes")
        else:
            print("RESULT: PASS - CMS requests working properly")

        browser.close()

if __name__ == "__main__":
    run_check()