from playwright.sync_api import sync_playwright

PAGE_URL = "https://my.hiredly.com/about-us"
CMS_URL = "https://cms.hiredly.com"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page    = browser.new_page()

        # Track CMS status
        cms_requests_found = False
        cms_cors_errors = False
        cms_responses = []
        #all_requests = []

        # 1) Listen for console messages - only CMS-related CORS errors
        def on_console(msg):
            nonlocal cms_cors_errors
            # Show ERRORS related to CORS involving cms.hiredl.com
            if "has been blocked by CORS policy" in msg.text and "cms.hiredly.com" in msg.text:
                print("CMS CORS Error:", msg.text)
                cms_cors_errors = True
        page.on("console", on_console)
        
        def on_request(request):
            #all_requests.append(request.url)
            #print(f"Request: {request.url}") # Debugging
            pass

        # 2) Only inspect CMS responses
        def on_response(response):
            nonlocal cms_requests_found
            url = response.url
            #print(f"Response: {url} - Status: {response.status}") 
            if "cms.hiredly.com" in url:
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
        page.on("request", on_request)

        # 3) Navigate and wait until network is idle
        print(f"Checking CMS requests from: {PAGE_URL}")
        page.goto(PAGE_URL,timeout=60000 ,wait_until="load")

        # 4) Give extra time for any late console messages
        page.wait_for_timeout(2000)

        # 5) Determine PASS/FAIL
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
    main()