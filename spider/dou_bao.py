import asyncio

from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from util import crawler_util


class DouBao:

    async def cleanup_function(self):
        await self.playwright.stop()


    def __init__(self):
        self.playwright = None
        self.browser = None
        self.share_id = None
        self.inited = False

    async def create_playwright(self):
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=crawler_util.headless)
        self.browser = browser
        self.playwright = playwright


    async def handle_response(self,response):
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


    async def data_append(self,page, list_):
        # 3. 5秒内等待 div.dc433409 加载，超时则抛TimeoutError
        target_div = await page.wait_for_selector(
            selector='[data-testid="canvas_panel_container"] [data-testid="search-text-item"]',  # 目标元素选择器
            timeout=5000  # 超时时间：5000毫秒（5秒）
        )

        # await page.screenshot(path="full_page.png", full_page=True)

        # 定位目标div下所有 <a> 标签（即包含链接和标题的标签）
        a_tags = await target_div.query_selector('../ ..')
        a_tags = await a_tags.query_selector_all('[data-testid="search-text-item"] a ')
        # think-block-container

        # 遍历a标签，提取链接和标题
        for a_tag in a_tags:
            # 提取链接：a标签的href属性
            url = await a_tag.get_attribute("href")
            # 提取标题：a标签内 class="search-view-card__title" 的div文本（标题容器）
            title_elem = await a_tag.query_selector('//div[contains(@class,"search-item-title")]')  # 定位标题元素
            if title_elem:
                title = await title_elem.text_content()
                title = title.strip()
            else:
                title = '无标题'


            source_elem = await a_tag.query_selector('//span[contains(@class,"footer-title")]')
            if source_elem:
                source = await source_elem.text_content()
                source = source.strip()
            else:
                source = '无来源'

            dict_ = {'title': title, 'url': url, 'source': source}
            list_.append(dict_)

    async def handle_data(self, page, question):
        deep_thinking_button = await page.wait_for_selector('[data-testid="use-deep-thinking-switch-btn"] > button',
                                                      timeout=30000)

        await deep_thinking_button.click()

        textarea = page.locator('textarea.semi-input-textarea')
        await textarea.fill(question)

        await page.wait_for_timeout(100)
        await page.locator("#flow-end-msg-send").click()

        # 等待分享元素加载，设置超时时间为100秒(100000毫秒)
        # page.wait_for_selector(
        #     'div.message-action-button-main [data-testid="message_action_share"]',
        #     # waiting til the share button available
        #     timeout=100000  # 100秒超时
        # )
        # 等待分享元素加载，设置超时时间为100秒(100000毫秒)
        await page.wait_for_selector(
            '[data-testid="suggest_message_list"]',
            # waiting til the share button available
            timeout=100000  # 100秒超时
        )
        dict_final = {'runStatus': 1, 'article': ''}

        list_ = []

        nodes = await page.query_selector_all(
            '[data-testid="receive_message"] [data-testid="message_content"] > div > [data-render-engine="node"]')
        node_size = len(nodes)

        if node_size == 0:
            nodes = await page.query_selector_all(
                '[data-testid="receive_message"] [data-testid="message_content"] > div > div')
            node_size = len(nodes)
            receive_message = nodes[node_size - 2]
        else:
            receive_message = await nodes[node_size - 2].wait_for_selector(
                ' > [data-testid="message_text_content"].flow-markdown-body')

        reference_element = await nodes[node_size - 1].query_selector('[data-testid="search-reference-ui"]')

        # 获取文本内容（不包含 HTML 标签）
        article = await receive_message.inner_text()


        try:
            await reference_element.click(timeout=1000)
            await self.data_append(page, list_)
        except Exception as e:
            print(e)

        await page.set_viewport_size({"width": 1920, "height": 1080})
        screenshot = await crawler_util.image_save_as(page)
        dict_final['screenshot'] = screenshot

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


    async def run_once(self, question: str) -> dict:
        if not self.inited:
            await self.create_playwright()
            self.inited = True

        async with await self.browser.new_context(
                # storage_state=self.storage_state,
                user_agent=crawler_util.get_random_user_agent()) as context:

            await Stealth().apply_stealth_async(context)
            page = await context.new_page()
            try:
                # page.set_viewport_size({"width": 1920, "height": 1080})
                await page.goto("https://www.doubao.com/chat/")
                page.on("dialog", lambda dialog: dialog.dismiss())
                # page.on("response", self.handle_response)  # Register the handler
                return await self.handle_data(page, question)
            finally:
                await page.close()


async def main():
    crawler_util.headless = False

    db = DouBao()

    q = "上海现在换电车还有什么官方补贴？"
    rs = await db.run_once(q)
    print(rs)

if __name__ == '__main__':
    asyncio.run(main())
