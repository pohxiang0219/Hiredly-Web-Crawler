from playwright.sync_api import sync_playwright
import time

PAGE_URL       = "https://my.hiredly.com/about-us"
CMS_URL        = "https://cms.hiredly.com"
MAX_RETRIES    = 3
RETRY_DELAY    = 3  # seconds

def run_check():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page    = browser.new_page()

        cms_requests_found = False
        cms_cors_errors    = False
        cms_responses      = []

        # 0) Catch _any_ request made to CMS—so even blocked preflights count as “found”
        def on_request(request):
            nonlocal cms_requests_found
            if CMS_URL in request.url:
                cms_requests_found = True
                print(f"→ CMS request detected: {request.method} {request.url}")
        page.on("request", on_request)

        # 1) Listen for CMS-related CORS console errors
        def on_console(msg):
            nonlocal cms_cors_errors
            text = msg.text.lower()
            if "blocked by cors policy" in text and CMS_URL in text:
                print("⚠️ CMS CORS Error:", msg.text)
                cms_cors_errors = True
        page.on("console", on_console)

        # 2) Listen for CMS responses (successful or error status codes)
        def on_response(response):
            url = response.url
            if CMS_URL in url:
                status      = response.status
                aca_origin  = response.headers.get("access-control-allow-origin")
                aca_headers = response.headers.get("access-control-allow-headers")
                print(f"↪️ CMS Response: {url}  [status={status}]")
                print(f"   ACAO: {aca_origin}")
                print(f"   ACAH: {aca_headers}")
                cms_responses.append({
                    'url':    url,
                    'status': status,
                    'acao':   aca_origin,
                    'acah':   aca_headers
                })
        page.on("response", on_response)

        # 3) Navigate with retries
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                print(f"Attempt {attempt}: navigating to {PAGE_URL}")
                page.goto(PAGE_URL, timeout=30000, wait_until="domcontentloaded")
                page.wait_for_timeout(5000)
                break
            except Exception as e:
                print(f"❌ Load error (attempt {attempt}): {e}")
                if attempt < MAX_RETRIES:
                    print(f"Retrying in {RETRY_DELAY}s…")
                    time.sleep(RETRY_DELAY)
                else:
                    print("RESULT: FAILED - Page failed to load after retries")
                    browser.close()
                    return

        # 4) Final evaluation
        if cms_cors_errors:
            print("RESULT: FAILED - CMS CORS errors detected")
        elif not cms_requests_found:
            print("RESULT: FAILED - No CMS requests detected at all")
        elif any(r['status'] >= 400 for r in cms_responses):
            print("RESULT: FAILED - CMS returned HTTP error codes")
        else:
            print("RESULT: PASS - CMS requests succeeded and no CORS errors")

        browser.close()

if __name__ == "__main__":
    run_check()