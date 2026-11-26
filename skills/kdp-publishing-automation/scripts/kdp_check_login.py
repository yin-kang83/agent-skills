# -*- coding: utf-8 -*-
"""检查 KDP 登录态与当前页面（CDP 9223）。

用法：python kdp_check_login.py
退出码：0 = 已登录；1 = 未登录 / 连不上
"""
import os
import sys

from playwright.sync_api import sync_playwright

CDP = "http://127.0.0.1:9223"
SHOT = r"D:\tools\kdp_shots"
os.makedirs(SHOT, exist_ok=True)

with sync_playwright() as p:
    try:
        b = p.chromium.connect_over_cdp(CDP)
    except Exception as e:
        print("CDP FAIL:", str(e)[:200])
        sys.exit(1)

    ctx = b.contexts[0]
    page = ctx.pages[-1]
    page.bring_to_front()
    print("URL:", page.url)
    print("TITLE:", page.title())

    if "signin" in page.url or "ap/signin" in page.url:
        print("STATUS: NOT LOGGED IN (登录页)")
        sys.exit(1)

    if "kdp.amazon.com" in page.url:
        body = page.inner_text("body")[:300].replace("\n", " | ")
        if "Sign out" in body or "Bookshelf" in body:
            print("STATUS: LOGGED IN")
            page.screenshot(path=os.path.join(SHOT, "login_ok.png"))
            sys.exit(0)

    print("STATUS: UNKNOWN")
    sys.exit(1)
