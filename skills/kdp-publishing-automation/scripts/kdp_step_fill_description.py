# -*- coding: utf-8 -*-
"""填 KDP 简介（CKEditor iframe）。"""
import os
from playwright.sync_api import sync_playwright

SHOT = r"D:\tools\kdp_shots"

DESC = """一個管死人生意的九品小吏，發現自家的帳簿被人改了。

輪迴殿經卷司錄事顧行舟，抄了六年死錄，抄錯過兩筆，每一筆折一年陽壽。他守的規矩只有一條：不許追問。

直到一個夜裡，他抄到第四十八張死錄——同一個名字，同一個死因，同一個判詞，死期卻差七天。一份是正常歸檔的舊卷，一份的背後蓋著校勘司的印。

他去問主簿，主簿當著他的面把廢卷燒了。火裡最後顯出來的三個字，不是死者的名字，是他自己的。

從此他知道了三件事：幽冥的生死簿有兩層墨；改墨的人用的是一枚被磨掉一個點的仿印；而這座殿底下壓著的，是一位被所有人忘了名字的舊神。

他往上查，查到的人都死了；他往下查，查到一座廟。廟裡擔著三千一百四十七個不能走的魂，廟門上寫著四個字：遇僧讓路。

一個連自己都不在生死簿上的人，要拿什麼去查一樁冥府做了三百年的帳？

——本書為《輪迴殿》第一卷，共十三章。

【本書特色】
· 東方志怪 × 官場懸疑：不是打怪升級，是查帳、對印、翻舊檔
· 世界觀看得見：六道、業帳、陰壽、度牒、銷號，每一個設定都落到具體手續上
· 每一章一個鉤子：兩份死錄、假印、磨印房、空殼、斷詞、假死、執筆

【適合誰讀】
喜歡《長安十二時辰》式的時限壓力、《大明王朝》式的官僚系統、中式志怪氛圍的讀者。"""

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9223")
    page = b.contexts[0].pages[-1]
    page.bring_to_front()

    # CKEditor iframe
    frames = page.frames
    print("frames:", len(frames))
    target = None
    for f in frames:
        if "cke_wysiwyg" in (f.name or "") or "editable" in (f.name or ""):
            target = f
            print("found frame by name:", f.name, f.url[:60])
    if target is None:
        for f in frames:
            try:
                body = f.locator("body")
                if body.count() > 0 and "wysiwyg" in f.url:
                    target = f
                    print("found frame by url:", f.url[:80])
                    break
            except Exception:
                pass

    if target is None:
        # 从 iframe 元素取 frame_locator（CKEditor）
        print("iframe count:", page.locator("iframe.cke_wysiwyg_frame").count())
        body = page.frame_locator("iframe.cke_wysiwyg_frame").locator("body")
    else:
        body = target

    print("body count:", body.count())
    body.click()
    page.wait_for_timeout(300)

    # 输入：按段落粘贴（用 insert_text 避免快捷键冲突）
    paras = [x for x in DESC.split("\n") if x.strip()]
    for i, para in enumerate(paras):
        if i > 0:
            page.keyboard.press("Enter")
        page.keyboard.insert_text(para)
    print("typed paragraphs:", len(paras))
    page.wait_for_timeout(2000)

    # 读回 hidden input 同步值
    val = page.evaluate("""() => {
        const el = document.querySelector('input[name="data[description]"]');
        return el ? el.value.length : -1;
    }""")
    print("hidden description length:", val)

    # 读 iframe 内容长度
    txt = body.inner_text()
    print("iframe text length:", len(txt))
    print("first 80:", txt[:80].replace("\n", " "))

    page.screenshot(path=os.path.join(SHOT, "kdp_12_desc_filled.png"))
    print("SHOT saved")
