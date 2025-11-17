import asyncio
import json
import queue
import re
import time

import httpx
import requests
from requests_sse import EventSource
from playwright.sync_api import Playwright, sync_playwright, expect
import crawler_util


history_data = None

def ini_button(page, css_class):
    button = page.wait_for_selector(
        selector=css_class,
        timeout=5000  # 超时时间：5000毫秒（5秒）
    )
    button.click()

def handle_response(response):
    global history_data
    if "aichat/api/conversation" in response.url and response.status == 200 :
        print(f"Intercepted API response: {response.url}")

        try:
            # body = response.body()
            res = response.text()
            for line in res.split("\n"):
                if '"referenceList":' in line:
                    history_data = json.loads(line.lstrip('data:'))
        except Exception as e:
            print(e)
            print('######')

async def stream_events(url, headers, json_data):
    global history_data
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", url,headers=headers, json=json_data) as response:
            response.raise_for_status()  # Raise an exception for bad status codes
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    # event_data = line[len("data:"):].strip()
                    # print(f"Received event: {event_data}")
                    if '"referenceList":' in line:
                        history_data = json.loads(line.lstrip('data:'))




# Listen for the 'requestfinished' event
def handle_request(request):
    global history_data
    # Check if the request has a response
    if 'aichat/api/conversation' in request.url:
        try:
            asyncio.ensure_future(stream_events(request.url, request.headers, json.loads(request.post_data)))
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


def run_once(playwright: Playwright, question: str) -> None:
    global history_data
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    # context = browser.new_context(storage_state="baidu.json")
    page = context.new_page()
    # page.on("response", handle_response)  # Register the handler
    page.on("request", handle_request)  # Register the handler

    page.goto("https://chat.baidu.com/search")


    all_requests = []
    page.on("request", lambda request: all_requests.append(request.url))


    deep_think = True
    model_name = 'DeepSeek-V3.2'
    model_name = '文心 4.5 Turbo'
    internet_search = True


    if deep_think:
        page.wait_for_selector('.internet-search-icon',timeout=8000).click()

    else:
        crawler_util.select_drop_down_item(page,
                                           '.model-select-toggle',
                                           '.input-capsules-model-list-item-title',
                                           model_name)


        online_search_button = page.wait_for_selector('.cos-switcher', timeout=10000)
        if internet_search and 'checked' not in online_search_button.get_attribute("class").strip():
            online_search_button.click()


    textarea = page.locator('#chat-textarea')
    textarea.fill(question)

    page.wait_for_timeout(100)
    page.locator("#chat-submit-button-ai").click()

    # 等待元素加载，设置超时时间为100秒(100000毫秒)
    element = page.wait_for_selector(
        ".cs-answer-hover-menu-container .cos-icon-exchange", # waiting til the share button available
        timeout=100000  # 100秒超时
    )

    # print(all_requests)

    entrys = page.query_selector_all('.ai-entry .ai-entry-block')
    entrys.pop(0) # ignore first div infomation
    element = page.query_selector('[data-show-ext*="answer_origin_button"]')
    # 获取元素的文本内容（不包含 HTML 标签）
    article = '\n'.join([e.inner_text() for e in entrys])

    dict_final = {}
    dict_final['status']  = '0'
    dict_final['article'] = article
    list_ = []



    page.wait_for_selector(
        ".cs-answer-hover-menu-container .cos-icon-exchange",  # waiting til the share button available
        timeout=100000  # 100秒超时
    )

    page.wait_for_selector('[data-show-ext*="answer_origin_button"]',timeout=2000).click()
    page.screenshot(path="full_page.png", full_page=True)

    if history_data:
        rs = crawler_util.find_key_in_json(history_data, "referenceList")
        for r in rs[0]:
            dict_ = {}
            dict_['title'] = r.get('text')
            dict_['url'] = r.get('url')
            list_.append(dict_)

    dict_final['list'] = list_
    return  dict_final

if __name__ == '__main__':

    with sync_playwright() as playwright:
        question = "给出2025年9月22号，食品安全相关的负面新闻有哪些，给出标题和链接。"
        dict_final = run_once(playwright, question)
        print(dict_final)