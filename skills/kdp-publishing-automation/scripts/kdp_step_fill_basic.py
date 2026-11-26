# -*- coding: utf-8 -*-
"""KDP 第 3 步：填 details 页基础字段（语言/书名/副标/作者/关键词/版权/成人）。"""
import os
from playwright.sync_api import sync_playwright

SHOT = r"D:\tools\kdp_shots"
os.makedirs(SHOT, exist_ok=True)

TITLE = "輪迴殿"
SUBTITLE = "卷一：兩份死錄"
AUTHOR = "柏下客"
KEYWORDS = ["東方玄幻", "幽冥志怪", "官場懸疑", "中國神話", "陰陽兩界", "推理探案", "長篇小說"]

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9223")
    page = b.contexts[0].pages[-1]
    page.bring_to_front()
    page.wait_for_timeout(800)
    print("URL:", page.url)

    # 1) 语言
    try:
        page.select_option("#data-language-native", label="Chinese (Traditional) (Beta)")
        print("OK language")
    except Exception as e:
        print("FAIL language", str(e)[:120])

    page.wait_for_timeout(1200)

    # 2) 书名
    page.fill("#data-title", TITLE)
    print("OK title:", page.input_value("#data-title"))

    # 3) 副标
    try:
        page.fill("#data-subtitle", SUBTITLE)
        print("OK subtitle:", page.input_value("#data-subtitle"))
    except Exception as e:
        print("FAIL subtitle", str(e)[:100])

    # 4) 作者（中文笔名：First name 填全名，Last name 留空）
    try:
        page.fill("#data-primary-author-first-name", AUTHOR)
        print("OK author first:", page.input_value("#data-primary-author-first-name"))
    except Exception as e:
        print("FAIL author", str(e)[:100])

    # 5) 关键词
    for i, kw in enumerate(KEYWORDS):
        sel = f"#data-keywords-{i}"
        try:
            page.fill(sel, kw)
        except Exception as e:
            print("FAIL kw", i, str(e)[:60])
    print("OK keywords")

    # 6) 版权：非公有领域
    try:
        page.check("#non-public-domain")
        print("OK public-domain radio")
    except Exception as e:
        print("FAIL pd", str(e)[:100])

    # 7) 成人内容：No
    try:
        page.evaluate("""() => {
            const rs = document.querySelectorAll('input[name="data[is_adult_content]-radio"]');
            for (const r of rs) { if (r.value === 'false') { r.click(); return true; } }
            return false;
        }""")
        print("OK adult-content No")
    except Exception as e:
        print("FAIL adult", str(e)[:100])

    page.wait_for_timeout(1000)
    page.screenshot(path=os.path.join(SHOT, "kdp_07_basic_filled.png"))
    print("SHOT saved")

    # 打印当前关键字段值核对
    for sel in ["#data-title", "#data-subtitle", "#data-primary-author-first-name"]:
        print(sel, "=", repr(page.input_value(sel)))
