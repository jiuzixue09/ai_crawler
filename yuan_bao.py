import atexit
import time

from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

import crawler_util


class YuanBao:
    def cleanup_function(self):
        self.context.close()
        self.playwright.stop()

    def __init__(self):
        storage_state = "cookies/yuanbao/yuanbao_1.json"
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=crawler_util.headless)
        context = browser.new_context(storage_state=storage_state,
                                      user_agent=crawler_util.get_random_user_agent())

        self.context = context
        self.playwright = playwright
        self.share_id = None

        atexit.register(self.cleanup_function)


    def handle_response(self,response):
        # https://yuanbao.tencent.com/api/conversations/v2/share
        if "api/conversations/v2/share" in response.url and response.status == 200:
            print(f"Intercepted API response: {response.url}")
            try:
                res = response.json()
                if res:
                    if 'shareId' in res:
                        self.share_id = res['shareId']
                    else:
                        data = res['data']
                        if data and 'pre_share_id' in data:
                            self.share_id = data['pre_share_id']
                        if data and 'share_id' in data:
                            self.share_id = data['share_id']
            except Exception as e:
                print(e)

    def run_once(self, question: str) -> dict:
        page = self.context.new_page()
        stealth_sync(page)
        try:

            page.goto("https://yuanbao.tencent.com/")

            page.on("response", self.handle_response)  # Register the handler
            page.on("dialog", lambda dialog: dialog.accept())
            return self.handle_data(page, question)
        finally:
            page.close()


    def handle_data(self, page, question: str) -> dict:

        model_name = 'DeepSeek'
        deep_think = True
        internet_search = True
        internet_search_name = 'Auto'

        crawler_util.select_drop_down_item(page,
                                           '[dt-button-id="model_switch"]',
                                           'div.drop-down-item__name',
                                           model_name)

        deep_think_button = page.wait_for_selector('[dt-button-id="deep_think"]', timeout=10000)
        if deep_think and 'checked' not in deep_think_button.get_attribute("class").strip():
            deep_think_button.click()

        online_search_button = page.wait_for_selector('[dt-button-id="online_search"]', timeout=10000)
        if internet_search and 'checked' not in online_search_button.get_attribute("class").strip():
            online_search_button.click()

        crawler_util.select_drop_down_item(page,
                                           'div.yb-switch-internet-search-btn__right',
                                           'div.drop-down-item__name',
                                           internet_search_name)

        textarea = page.locator('div.ql-editor')
        textarea.fill(question)

        page.wait_for_timeout(100)
        page.locator("#yuanbao-send-btn").click()

        share_button = page.wait_for_selector('.agent-chat__toolbar_new .agent-chat__toolbar__share', timeout=100 * 1000)

        markdown_divs = page.locator('div.hyc-component-reasoner__text')
        if not markdown_divs.is_visible():
            markdown_divs = page.locator('.hyc-component-deepsearch-cot > .hyc-content-md-done')

        # 获取第二个元素的文本内容（不包含 HTML 标签）
        article = markdown_divs.inner_text()

        dict_final = {'status': '0', 'article': article}
        list_ = []

        element = page.locator(".agent-chat__search-guid-tool__source")
        try:
            element.wait_for(state='visible', timeout=60 * 1000) #这行代码主要是让程序休眠时间一段时间，防止账号被封
        except Exception as e:
            print(e)

        if element and element.is_visible():
            element.click()
            # 3. 5秒内等待 div.dc433409 加载，超时则抛TimeoutError
            target_div = page.wait_for_selector(
                selector='[id="chatReferenceList"] ul',  # 目标元素选择器
                timeout=5000  # 超时时间：5000毫秒（5秒）
            )

            client = page.context.new_cdp_session(page)

            # Set the zoom level (e.g., 0.75 for 75% zoom, simulating Ctrl -)
            client.send("Emulation.setPageScaleFactor", {"pageScaleFactor": 0.5})

            page.screenshot(path="full_page.png", full_page=True)

            # 定位目标div下所有 <a> 标签（即包含链接和标题的标签）
            a_tags = target_div.query_selector_all("li")

            # 遍历a标签，提取链接和标题
            for a_tag in a_tags:
                # 提取链接：a标签的href属性
                url = a_tag.get_attribute("dt-ext6")
                # 提取标题：a标签内 class="search-view-card__title" 的div文本（标题容器）
                title_elem = a_tag.query_selector(".hyc-common-markdown__ref_card-title")  # 定位标题元素
                title = title_elem.text_content().strip() if title_elem else "无标题"  # 处理标题为空的情况
                dict_ = {}
                dict_['title'] = title
                dict_['url'] = url
                list_.append(dict_)
                dict_final['list'] = list_

        share_button.click()
        copy_button = page.wait_for_selector(
            '.agent-chat__share-bar__content__center .agent-chat__share-bar__item__logo:first-child')

        for i in range(1, 5):
            if self.share_id:
                break
            else:
                time.sleep(i)
                copy_button.click()

        if self.share_id:
            share_link = f'https://yb.tencent.com/s/{self.share_id}'
            dict_final['share_link'] = share_link

        return dict_final


if __name__ == '__main__':
    crawler_util.headless = False
    yb = YuanBao()

    q = "消费者对新能源汽车的续航焦虑如何缓解？"
    rs = yb.run_once(q)
    print(rs)
