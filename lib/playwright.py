from playwright.sync_api import sync_playwright

PAGE_URL = "https://my.hiredly.com/about-us"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page    = browser.new_page()

        # 1) Listen for console messages
        def on_console(msg):
            # We're only interested in CORS-related errors
            if "has been blocked by CORS policy" in msg.text:
                print("⛔ CORS Error:", msg.text)
        page.on("console", on_console)

        # 2) Optionally, inspect each response's headers
        def on_response(response):
            url = response.url
            if "cms.hiredly.com" in url:
                aca_origin = response.headers.get("access-control-allow-origin")
                print(f"{url} → ACAO: {aca_origin}")
        page.on("response", on_response)

        # 3) Navigate and wait until network is idle
        page.goto(PAGE_URL, wait_until="networkidle")

        # 4) (Optional) Give extra time for any late console messages
        page.wait_for_timeout(2000)

        browser.close()

if __name__ == "__main__":
    main()
