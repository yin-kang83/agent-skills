# -*- coding: utf-8 -*-
"""KDP 一键上传（详情页）——《輪迴殿》卷一 繁体版。

用法：
    python kdp_upload_all.py            # 跑详情页全流程
    python kdp_upload_all.py --dry      # 只检查配置与页面，不点击

前置：
    1. Edge 已用默认 profile 启动并开启 CDP 9223
    2. 用户已登录 KDP
    3. 每周标题限额未满（周日 00:00 UTC 重置）

阶段：
    A. Bookshelf -> Create new title -> Kindle eBook -> 详情页
    B. 填详情页全部字段
    C. 保存并继续（进入内容页，后续步骤见 stage 函数）
"""
import json
import os
import sys
import time

from playwright.sync_api import sync_playwright

CDP = "http://127.0.0.1:9223"
CFG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kdp_config.json")
SHOT = r"D:\tools\kdp_shots"
os.makedirs(SHOT, exist_ok=True)

DRY = "--dry" in sys.argv

CFG = json.load(open(CFG_PATH, encoding="utf-8"))


def shot(page, name):
    p = os.path.join(SHOT, name)
    page.screenshot(path=p)
    print("  SHOT:", p)


# ---------- JS 工具 ----------
JS_SELECT_TITLE = """
(args) => {
    const [idx, label] = args;
    const modal = document.querySelector('[role=dialog]') || document;
    const sels = modal.querySelectorAll('select');
    if (!sels[idx]) return {ok:false, reason:'no select '+idx};
    const s = sels[idx];
    const hit = Array.from(s.options).find(o => o.text.trim() === label);
    if (!hit) return {ok:false, reason:'no option', opts: Array.from(s.options).map(o=>o.text)};
    s.value = hit.value;
    s.dispatchEvent(new Event('change', {bubbles:true}));
    return {ok:true, value:hit.value};
}
"""

JS_SET_LANG = """
(label) => {
    const s = document.querySelector('#data-language-native');
    if (!s) return {ok:false};
    const hit = Array.from(s.options).find(o => o.text.trim() === label);
    if (!hit) return {ok:false, opts: Array.from(s.options).map(o=>o.text)};
    s.value = hit.value;
    s.dispatchEvent(new Event('change', {bubbles:true}));
    const d = document.querySelector("input[aria-label='language-dropdown-editable-text']");
    if (d) { d.value = hit.text; d.dispatchEvent(new Event('input', {bubbles:true})); d.dispatchEvent(new Event('change', {bubbles:true})); }
    return {ok:true, value:hit.value};
}
"""

JS_CHECKBOX = """
(args) => {
    const [label, want] = args;
    const modal = document.querySelector('[role=dialog]') || document;
    for (const c of modal.querySelectorAll('input[type=checkbox]')) {
        const lab = c.closest('label');
        if (lab && lab.innerText.trim() === label) {
            if (c.checked !== want) c.click();
            return {ok:true, checked:c.checked};
        }
    }
    return {ok:false, reason:'not found:'+label};
}
"""

JS_CLICK_TEXT = """
(text) => {
    const cand = document.querySelectorAll('button, .a-button-text, span.a-button-inner, input[type=submit]');
    for (const el of cand) {
        const t = (el.innerText || el.value || '').trim();
        if (t === text) { el.click(); return {ok:true, tag:el.tagName}; }
    }
    return {ok:false};
}
"""


def ensure_details_page(page):
    print("[A] 进入详情页")
    if "/title-setup/kindle/new/details" not in page.url:
        page.goto("https://kdp.amazon.com/en_US/bookshelf", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)
        page.get_by_role("button", name="Create new title or series").first.click()
        page.wait_for_timeout(3000)
        page.get_by_role("button", name="Create eBook").first.click()
        page.wait_for_timeout(4000)
    print("  URL:", page.url)


def fill_details(page):
    print("[B] 填详情页")

    # 语言
    r = page.evaluate(JS_SET_LANG, CFG["language"])
    print("  language:", r.get("ok"), r.get("value"))

    # 书名 / 副标 / 作者
    page.fill("#data-title", CFG["title"])
    page.fill("#data-subtitle", CFG["subtitle"])
    page.fill("#data-primary-author-first-name", CFG["author_first_name"])
    if CFG["author_last_name"]:
        page.fill("#data-primary-author-last-name", CFG["author_last_name"])
    print("  title:", page.input_value("#data-title"))

    # 关键词
    for i, kw in enumerate(CFG["keywords"][:7]):
        page.fill(f"#data-keywords-{i}", kw)
    print("  keywords: 7 个")

    # 简介（CKEditor）
    body = page.frame_locator("iframe.cke_wysiwyg_frame").locator("body")
    body.click()
    paras = [x for x in CFG["description"].split("\n") if x.strip()]
    for i, para in enumerate(paras):
        if i > 0:
            page.keyboard.press("Enter")
        page.keyboard.insert_text(para)
    print("  description:", len(paras), "段")

    # 版权 / 成人
    page.check("#non-public-domain")
    page.evaluate("""() => {
        document.querySelectorAll('input[name="data[is_adult_content]-radio"]').forEach(r => {
            if (r.value === 'false') r.click();
        });
    }""")
    print("  rights/adult: ok")


def fill_categories(page):
    print("[C] 分类")
    for idx, cat in enumerate(CFG["categories"]):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(600)
        page.locator("#categories-modal-button").first.click()
        page.wait_for_timeout(2500)

        if idx > 0:
            page.locator("[role=dialog] button:has-text('Add another category')").first.click()
            page.wait_for_timeout(2500)

        n = page.evaluate("() => (document.querySelector('[role=dialog]')||document).querySelectorAll('select').length")
        base = n - 2 if idx > 0 else 0
        print(f"  cat{idx} ({cat['note']}): selects={n} base={base}")

        page.evaluate(JS_SELECT_TITLE, [base, cat["l1"]])
        page.wait_for_timeout(2200)
        page.evaluate(JS_SELECT_TITLE, [base + 1, cat["l2"]])
        page.wait_for_timeout(2500)
        r = page.evaluate(JS_CHECKBOX, [cat["leaf"], True])
        print("    leaf:", cat["leaf"], r)

        page.locator("[role=dialog] button:has-text('Save categories')").first.click()
        page.wait_for_timeout(3500)
        txt = page.evaluate("""() => {
            const b = document.body.innerText; const i = b.indexOf("Your title's current categories");
            return i >= 0 ? b.slice(i, i + 300) : '';
        }""")
        print("    saved:", txt.replace("\n", " | ")[:220])


def main():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP)
        ctx = browser.contexts[0]
        page = ctx.pages[-1]
        page.bring_to_front()

        ensure_details_page(page)
        if DRY:
            print("DRY: 停在详情页，不填")
            shot(page, "dry_details.png")
            return

        fill_details(page)
        fill_categories(page)

        shot(page, "kdp_details_done.png")
        print("[D] 详情页完成。下一步：Save and Continue -> 内容页")
        print("     若显示 Title creation limit reached，说明本周限额未重置。")


if __name__ == "__main__":
    main()
