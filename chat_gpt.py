import atexit
import time

from playwright.sync_api import sync_playwright
import crawler_util


class ChatGpt:
    def cleanup_function(self):
        crawler_util.save_cookies(self.context, self.storage_state)
        self.context.close()
        self.playwright.stop()

    def __init__(self):
        self.storage_state = "cookies/chatgpt/chatgpt.json"
        playwright = sync_playwright().start()
        browser = playwright.chromium.connect_over_cdp("http://127.0.0.1:9222")

        context = browser.contexts[0]

        self.context = context
        self.playwright = playwright
        self.share_id = None

        atexit.register(self.cleanup_function)


    def handle_response(self,response):
        #https://chatgpt.com/backend-api/share/post
        #https://chatgpt.com/backend-api/share/create
        #https://chatgpt.com/s/t_691edd5140b88191a60d1d0833fb4c8c
        if "/share/create" in response.url and response.status == 200 :
            print(f"Intercepted API response: {response.url}")
            try:
                res = response.json()
                if res:
                    if 'share_id' in res:
                        self.share_id = res['share_id']
                    else:
                        data = res['post']
                        if data and 'id' in data:
                            self.share_id = data['id']
            except Exception as e:
                print(e)

    def run_once(self, question: str) -> dict:

        if len(self.context.pages) > 0:
            page = self.context.pages[0]
        else:
            page = self.context.new_page()

        try:
            page.goto("https://chatgpt.com/")
            page.on("response", self.handle_response)  # Register the handler
            return self.handle_data(page, question)
        finally:
            page.close()

    def handle_data(self, page, question: str) -> dict:
        model_name = 'Thinking'

        crawler_util.select_drop_down_item(page,
                                           '#composer-plus-btn',
                                           '.flex .truncate',
                                           model_name)

        textarea = page.locator('#prompt-textarea')
        textarea.fill(question)

        page.wait_for_timeout(100)
        page.locator("#composer-submit-button").click()

        # 等待元素加载，设置超时时间为100秒(100000毫秒)
        page.wait_for_selector(
            '.justify-start [aria-label="Share"]', # waiting til the share button available
            timeout=100000  # 100秒超时
        )


        # ds-icon-button _7436101 bcc55ca1 ds-icon-button--disabled
        markdown_divs = page.locator('.markdown')

        # 获取第二个元素的文本内容（不包含 HTML 标签）
        article = markdown_divs.inner_text()

        dict_final = {}
        dict_final['status']  = '0'
        dict_final['article'] = article
        list_ = []

        element = page.wait_for_selector(
            '.flex-row-reverse',  # waiting til the share button available
            timeout=100000  # 100秒超时
        )
        if element:
            element.click()
            # 3. 5秒内等待 div.dc433409 加载，超时则抛TimeoutError
            target_div = page.wait_for_selector(
                selector='[slot="content"] ul',  # 目标元素选择器
                timeout=5000  # 超时时间：5000毫秒（5秒）
            )
            target_div.wait_for_element_state(state="visible")
            # 定位目标div下所有 <a> 标签（即包含链接和标题的标签）
            a_tags = target_div.query_selector_all("li a")

            time.sleep(1)
            page.screenshot(path="full_page.png", full_page=True)

            # 遍历a标签，提取链接和标题
            for a_tag in a_tags:
                # 提取链接：a标签的href属性
                url = a_tag.get_attribute("href")
                # 提取标题：a标签内 class="search-view-card__title" 的div文本（标题容器）
                title_elem = a_tag.query_selector(".break-words")  # 定位标题元素
                title = title_elem.text_content().strip() if title_elem else "无标题"  # 处理标题为空的情况
                dict_ = {'title': title, 'url': url}
                list_.append(dict_)
            dict_final['list'] = list_

        page.wait_for_selector('[aria-label="Share"]').click()
        page.wait_for_selector('button.relative .pointer-events-none').click()

        for i in range(1, 5):
            if self.share_id:
                break
            else:
                time.sleep(i)

        if self.share_id:
            share_link = f'https://chatgpt.com/share/{self.share_id}'
            dict_final['share_link'] = share_link


        return  dict_final


if __name__ == '__main__':
    q = "给出2025年9月22号，食品安全相关的负面新闻有哪些，给出标题和链接。"
    cg = ChatGpt()
    rs = cg.run_once(q)
    print(rs)
