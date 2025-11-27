import atexit
from playwright.sync_api import sync_playwright
import time

from playwright_stealth import Stealth

import crawler_util

class DeepSeek:

    def cleanup_function(self):
        self.context.close()
        self.playwright.stop()

    def __init__(self):
        storage_state = "cookies/deepseek/deepseek.json"
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=crawler_util.headless)
        context = browser.new_context(storage_state=storage_state,
                                      user_agent=crawler_util.get_random_user_agent())
        Stealth().apply_stealth_sync(context)

        self.context = context
        self.playwright = playwright

        atexit.register(self.cleanup_function)

    def run_once(self, question: str) -> dict:
        page = self.context.new_page()
        try:
            page.goto("https://chat.deepseek.com/")
            return self.handle_data(page, question)
        finally:
            page.close()

    def handle_data(self,page, question: str) -> dict:

        buttons = page.query_selector_all('button')

        for b in buttons:
            b.wait_for_element_state(state='visible')
            t = b.text_content().strip()
            if t in ['DeepThink','深度思考','Search','联网搜索']:
                b.click()

        textarea = page.locator('textarea.ds-scroll-area')
        textarea.fill(question)

        page.wait_for_timeout(100)
        page.get_by_role("button").nth(4).click()

        # 等待元素加载，设置超时时间为100秒(100000毫秒)
        share_element = page.wait_for_selector(
            "div.ds-flex > div.ds-flex > div.ds-icon-button:last-child",  # waiting til the share button available
            timeout=100000  # 100秒超时
        )
        # ds-icon-button _7436101 bcc55ca1 ds-icon-button--disabled
        markdown_divs = page.query_selector_all('.ds-message .ds-markdown')

        article = markdown_divs.pop().inner_text()

        dict_final = {'status': '0', 'article': article}
        list_ = []
        source_element = page.locator(
            "div.ds-scroll-area div.ds-message > div > div:has(.site_logo_back)"
        )

        if source_element and source_element.last.is_visible():
            try:
                source_element.last.click()
                target_div = page.wait_for_selector(
                    selector="div.scrollable div.ds-scroll-area",  # 目标元素选择器
                    timeout=5000  # 超时时间：5000毫秒（5秒）
                )

                page.screenshot(path="full_page.png", full_page=True)

                # 定位目标div下所有 <a> 标签（即包含链接和标题的标签）
                a_tags = target_div.query_selector_all("div a")  # 仅查询该div内部的a标签

                # 遍历a标签，提取链接和标题
                for a_tag in a_tags:
                    # 提取链接：a标签的href属性
                    url = a_tag.get_attribute("href")
                    # 提取标题：a标签内 class="search-view-card__title" 的div文本（标题容器）
                    title_elem = a_tag.query_selector("div.search-view-card__title")  # 定位标题元素
                    title = title_elem.text_content().strip() if title_elem else "无标题"  # 处理标题为空的情况
                    dict_ = {}
                    dict_['title'] = title
                    dict_['url'] = url
                    list_.append(dict_)
            except Exception as e:
                print(e)

        # share link from api https://chat.deepseek.com/api/v0/share/create
        share_element.click()
        page.wait_for_selector(".ds-basic-button--primary").click(timeout=2000)
        page.wait_for_selector(".ds-modal-content__footer button").click(timeout=2000)
        time.sleep(1)
        share_link = page.query_selector('.ds-modal-content__footer span').text_content().strip()
        dict_final['list'] = list_
        dict_final['share_link'] = share_link

        return dict_final


if __name__ == '__main__':
    crawler_util.headless = False
    # question = " 汽车元宇宙概念的落地场景？"
    q = "今年成都上牌补贴是多少钱？"
    ds = DeepSeek()
    rs = ds.run_once(q)
    print(rs)
