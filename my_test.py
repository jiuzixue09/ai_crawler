import asyncio
import json
import os.path
import subprocess

import requests
import urllib3
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from cf_clearance import sync_cf_retry, sync_stealth
from requests_sse import EventSource
import sseclient
import httpx



import crawler_util

command = ["bash", "/Users/dave/PycharmProjects/crawler/run_chrome.sh"]

try:
    p = subprocess.Popen(command,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # stdout, stderr = p.communicate(timeout=150)
    # print(stderr)
except FileNotFoundError:
    print(f"Error: Chrome executable not found at {command}")
except Exception as e:
    print(f"An error occurred: {e}")

print('running chrome')



with sync_playwright() as playwright:





    browser = playwright.chromium.connect_over_cdp("http://127.0.0.1:9222")
    default_context = browser.contexts[0]
    page = default_context.pages[0]


    context = playwright.chromium.launch_persistent_context(
        user_data_dir=r"/Users/dave/foo",  # 设置用户数据目录
        executable_path=chrome_path,  # Chrome 可执行文件路径
        accept_downloads=True,  # 允许下载
        headless=False,  # 非无头模式，即显示浏览器界面
        bypass_csp=True,  # 绕过 Content Security Policy
        slow_mo=10,  # 减速执行，便于调试
        args=[
            '--disable-blink-features=AutomationControlled',  # 禁用 Blink 功能控制
            '--remote-debugging-port=1234',  # 启用远程调试端口
            '--in-process-plugins',  # 插件在浏览器进程中运行
            '--allow-outdated-plugins',  # 允许使用过期插件
        ]
    )

# export https_proxy=http://127.0.0.1:7890 http_proxy=http://127.0.0.1:7890 all_proxy=socks5://127.0.0.1:7891
    #browser = playwright.chromium.launch(headless=False)
    #context = browser.new_context()
    page = context.new_page()
    sync_stealth(page)
    # Create a CDP session

    page.goto("https://www.scrapingcourse.com/cloudflare-challenge")
    res = sync_cf_retry(page)

    crawler_util.zoom_in(page,3)

    print(page.content())