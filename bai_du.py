import asyncio
import atexit
import json
import time

import httpx
import requests
from playwright.sync_api import sync_playwright
from playwright_stealth.stealth import Stealth

import crawler_util


class BaiDu:
    def cleanup_function(self):
        self.context.close()
        self.playwright.stop()

    def __init__(self):
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=crawler_util.headless)
        context = browser.new_context(user_agent=crawler_util.get_random_user_agent())

        Stealth().apply_stealth_sync(context)

        self.context = context
        self.playwright = playwright
        self.share_link = None
        self.history_data = None

        atexit.register(self.cleanup_function)

    def handle_response(self,response):
        # https://chat.baidu.com/aichat/api/shortURL
        if "aichat/api/shortURL" in response.url and response.status == 200 :
            print(f"Intercepted API response: {response.url}")
            try:
                res = response.json()
                if res:
                    data = res['data']
                    if data and 'short_url' in data:
                        self.share_link = data['short_url']
            except Exception as e:
                print(e)

    async def stream_events(self,url, headers, json_data):
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", url, headers=headers, json=json_data) as response:
                response.raise_for_status()  # Raise an exception for bad status codes
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        # event_data = line[len("data:"):].strip()
                        # print(f"Received event: {event_data}")
                        if '"referenceList":' in line:
                            self.history_data = json.loads(line.lstrip('data:'))


    def handle_request(self,request):
        # Check if the request has a response
        if 'aichat/api/conversation' in request.url:
            try:
                asyncio.ensure_future(self.stream_events(request.url, request.headers, json.loads(request.post_data)))
            except requests.exceptions.ConnectionError as e:
                print(f"Connection error: {e}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")


    def run_once(self, question: str) -> dict:
        page = self.context.new_page()
        try:

            page.goto("https://chat.baidu.com/search")
            page.on("request", self.handle_request)  # Register the handler
            page.on("response", self.handle_response)  # Register the handler
            return self.handle_data(page, question)
        finally:
            page.close()


    def handle_data(self,page, question: str) -> dict:
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
        page.wait_for_selector(
            ".cs-answer-hover-menu-container .cos-icon-exchange", # waiting til the share button available
            timeout=100000  # 100秒超时
        )

        # print(all_requests)

        entrys = page.query_selector_all('.ai-entry .ai-entry-block')
        entrys.pop(0) # ignore first div infomation

        try:
            element = page.wait_for_selector('[data-show-ext*="answer_origin_button"]', timeout=5000)
            element.click()
            time.sleep(1)
        except Exception as e:
            print(e)

        # 获取元素的文本内容（不包含 HTML 标签）
        article = '\n'.join([e.inner_text() for e in entrys])

        dict_final = {'status': '0', 'article': article}
        list_ = []

        page.screenshot(path="full_page.png", full_page=True)

        page.wait_for_selector('[data-show-ext*="share"]', timeout=2000).click()
        time.sleep(1)
        copy_button = page.get_by_role(
            "button",
            name="复制链接",  # 匹配按钮内的文本
            exact=True  # 精确匹配文本，避免模糊匹配其他按钮
        )

        copy_button.wait_for(state="visible")
        for i in range(1,5):
            if self.share_link:
                break
            else:
                time.sleep(i)
                copy_button.click()

        if self.history_data:
            rl = crawler_util.find_key_in_json(self.history_data, "referenceList")
            for r in rl[0]:
                dict_ = {'title': r.get('text'), 'url': r.get('url')}
                list_.append(dict_)

        if self.share_link:
            dict_final['share_link'] = self.share_link

        dict_final['list'] = list_
        return  dict_final


if __name__ == '__main__':
    crawler_util.headless = False
    bd = BaiDu()

    q = "浙江省委书记一连用了6个最"
    rs = bd.run_once(q)
    print(rs)
