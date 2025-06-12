import pytest
from playwright.sync_api import sync_playwright

def test_cms_requests():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        cms_requests_found = False
        cms_cors_errors = False
        cms_responses = []

        def on_console(msg):
            nonlocal cms_cors_errors
            if "has been blocked by CORS policy" in msg.text and "cms.hiredly.com" in msg.text:
                cms_cors_errors = True

        def on_response(response):
            nonlocal cms_requests_found
            url = response.url
            if "cms.hiredly.com" in url:
                cms_requests_found = True
                aca_origin = response.headers.get("access-control-allow-origin")
                status = response.status
                cms_responses.append({
                    'url': url,
                    'status': status,
                    'acao': aca_origin
                })

        page.on("console", on_console)
        page.on("response", on_response)

        page.goto("https://my.hiredly.com/about-us", timeout=60000, wait_until="load")
        page.wait_for_timeout(2000)

        assert cms_requests_found, "No CMS requests detected"
        assert not cms_cors_errors, "CMS CORS errors detected"
        assert all(resp['status'] < 400 for resp in cms_responses), "CMS returned error status codes"

        browser.close()