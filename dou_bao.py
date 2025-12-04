import time

from playwright._impl._api_structures import ProxySettings
from playwright.sync_api import sync_playwright, ViewportSize
import atexit

from playwright_stealth import Stealth

import crawler_util


class DouBao:

    def cleanup_function(self):
        self.playwright.stop()


    def __init__(self):

        self.share_id = None
        # self.storage_state = "cookies/doubao/doubao.json"
        playwright = sync_playwright().start()
        # proxy = ProxySettings(server=crawler_util.proxies['http'])
        # proxy = ProxySettings(server='http://f679.kdltps.com:15818/',
        #                       username='t12187413243075',password='yr4fjfks',
        #                       bypass="localhost,google-analytics.com")
        # proxy = ProxySettings(server='http://122.97.101.194:34642')

        browser = playwright.chromium.launch(headless=crawler_util.headless)
        self.browser = browser
        self.playwright = playwright

        atexit.register(self.cleanup_function)


    def handle_response(self,response):
        # https://www.doubao.com/samantha/thread/share/
        if "samantha/thread/share/" in response.url and response.status == 200 :
            print(f"Intercepted API response: {response.url}")
            try:
                res = response.json()
                if res:
                    data = res['data']
                    if data and 'pre_share_id' in data:
                        self.share_id = data['pre_share_id']
                    elif data and 'share_id' in data:
                        self.share_id = data['share_id']
            except Exception as e:
                print(e)


    def data_append(self,page, list_):
        # 3. 5秒内等待 div.dc433409 加载，超时则抛TimeoutError
        target_div = page.wait_for_selector(
            selector='[data-testid="canvas_panel_container"] [data-testid="search-text-item"]',  # 目标元素选择器
            timeout=5000  # 超时时间：5000毫秒（5秒）
        )

        page.screenshot(path="full_page.png", full_page=True)

        # 定位目标div下所有 <a> 标签（即包含链接和标题的标签）
        a_tags = target_div.query_selector('../ ..').query_selector_all('[data-testid="search-text-item"] a ')
        # think-block-container

        # 遍历a标签，提取链接和标题
        for a_tag in a_tags:
            # 提取链接：a标签的href属性
            url = a_tag.get_attribute("href")
            # 提取标题：a标签内 class="search-view-card__title" 的div文本（标题容器）
            title_elem = a_tag.query_selector('//div[contains(@class,"search-item-title")]')  # 定位标题元素
            title = title_elem.text_content().strip() if title_elem else "无标题"  # 处理标题为空的情况
            source_elem = a_tag.query_selector('//span[contains(@class,"footer-title")]')
            source = source_elem.text_content() if source_elem else '无来源'
            dict_ = {'title': title, 'url': url, 'source': source}
            list_.append(dict_)

    def handle_data(self, page, question):
        deep_thinking_button = page.wait_for_selector('[data-testid="use-deep-thinking-switch-btn"] > button',
                                                      timeout=30000)

        deep_thinking_button.click()

        textarea = page.locator('textarea.semi-input-textarea')
        textarea.fill(question)

        page.wait_for_timeout(100)
        page.locator("#flow-end-msg-send").click()

        # 等待分享元素加载，设置超时时间为100秒(100000毫秒)
        # page.wait_for_selector(
        #     'div.message-action-button-main [data-testid="message_action_share"]',
        #     # waiting til the share button available
        #     timeout=100000  # 100秒超时
        # )
        # 等待分享元素加载，设置超时时间为100秒(100000毫秒)
        page.wait_for_selector(
            '[data-testid="suggest_message_list"]',
            # waiting til the share button available
            timeout=100000  # 100秒超时
        )
        dict_final = {'status': 0, 'article': ''}

        list_ = []

        nodes = page.query_selector_all(
            '[data-testid="receive_message"] [data-testid="message_content"] > div > [data-render-engine="node"]')
        node_size = len(nodes)

        if node_size == 0:
            nodes = page.query_selector_all(
                '[data-testid="receive_message"] [data-testid="message_content"] > div > div')
            node_size = len(nodes)
            receive_message = nodes[node_size - 2]
        else:
            receive_message = nodes[node_size - 2].wait_for_selector(
                ' > [data-testid="message_text_content"].flow-markdown-body')

        reference_element = nodes[node_size - 1].query_selector('[data-testid="search-reference-ui"]')

        # 获取文本内容（不包含 HTML 标签）
        article = receive_message.inner_text()


        try:
            reference_element.click(timeout=1000)
            self.data_append(page, list_)
        except Exception as e:
            print(e)

        page.screenshot(path="full_page.png", full_page=True)
        # share_element = page.locator('div.message-action-button-main [data-testid="message_action_share"]')
        # share_element.click(timeout=5000)

        # page.wait_for_selector('[data-testid="thread_share_copy_btn"]')
        # for e in page.query_selector_all('[data-testid="thread_share_copy_btn"]'):
        #     try:
        #         e.click(timeout=1000)
        #     except Exception as e:
        #         pass

        # for i in range(1, 5):
        #     if self.share_id:
        #         break
        #     else:
        #         time.sleep(i)

        if self.share_id:
            share_link = f'https://www.doubao.com/thread/{self.share_id}'
            dict_final['share_link'] = share_link
        else:
            dict_final['share_link'] = '无分享链接'

        dict_final['article'] = article
        dict_final['list'] = list_
        return dict_final


    def run_once(self, question: str) -> dict:
        # browser = playwright.chromium.launch(headless=crawler_util.headless)
        context = self.browser.new_context(
            # storage_state=self.storage_state,
            user_agent=crawler_util.get_random_user_agent()
        )


        Stealth().apply_stealth_sync(context)
        page = context.new_page()
        try:
            # page.set_viewport_size({"width": 1920, "height": 1080})
            page.goto("https://www.doubao.com/chat/")
            page.on("response", self.handle_response)  # Register the handler
            return self.handle_data(page, question)
        finally:
            page.close()


if __name__ == '__main__':
    crawler_util.headless = False
    db =  DouBao()

    q = "上海现在换电车还有什么官方补贴？"
    rs = db.run_once(q)
    print(rs)