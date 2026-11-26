# -*- coding: utf-8 -*-
"""启动可被接管的 Edge（CDP 9222 + 持久化 profile），停在 KDP 登录页。

用法：python kdp_launch_edge.py
然后由用户在该窗口手动登录（邮箱 + 密码 + 短信验证码）。
登录完成后，另一个脚本可用 connect_over_cdp 接管。
"""
import os
import subprocess
import time

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
PROFILE = r"D:\tools\kdp_profile"
PORT = 9222
URL = "https://kdp.amazon.com/"

os.makedirs(PROFILE, exist_ok=True)

args = [
    EDGE,
    f"--remote-debugging-port={PORT}",
    f"--user-data-dir={PROFILE}",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-blink-features=AutomationControlled",
    "--start-maximized",
    URL,
]
proc = subprocess.Popen(args, close_fds=True)
print(f"Edge started pid={proc.pid} port={PORT} profile={PROFILE}")
time.sleep(4)
print(f"open http://127.0.0.1:{PORT}/json/version to verify CDP")
