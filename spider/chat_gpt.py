import asyncio

from playwright.async_api import async_playwright
from util import crawler_util


class ChatGpt:
    def cleanup_function(self):
        self.context.close()
        self.playwright.stop()

    def __init__(self):
        self.inited = False
        self.context = None
        self.share_id = None
        self.playwright = None


    async def create_playwright(self):
        storage_state = "cookies/chatgpt/chatgpt.json"
        # storage_state = None
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp("http://127.0.0.1:9222")

        if storage_state:
            context = await browser.new_context(storage_state=storage_state,
                                                user_agent=crawler_util.get_random_user_agent())
        else:
            context = await browser.new_context(user_agent=crawler_util.get_random_user_agent())

        self.context = context
        self.playwright = playwright


    async def handle_response(self,response):
        #https://chatgpt.com/backend-api/share/post
        #https://chatgpt.com/backend-api/share/create
        #https://chatgpt.com/s/t_691edd5140b88191a60d1d0833fb4c8c
        if "/share/create" in response.url and response.status == 200 :
            print(f"Intercepted API response: {response.url}")
            try:
                res = await response.json()
                if res:
                    if 'share_id' in res:
                        self.share_id = res['share_id']
                    else:
                        data = res['post']
                        if data and 'id' in data:
                            self.share_id = data['id']
            except Exception as e:
                print(e)


    async def handle_data(self, page, question: str) -> dict:
        model_name = 'Thinking'

        await crawler_util.select_drop_down_item(page,
                                           '#composer-plus-btn',
                                           '.flex .truncate',
                                                 model_name)

        textarea = page.locator('#prompt-textarea')
        await textarea.fill(question)

        await page.wait_for_timeout(100)
        await page.click("#composer-submit-button")

        # 等待元素加载，设置超时时间为100秒(100000毫秒)
        await page.wait_for_selector(
            '.justify-start [aria-label="Share"]', # waiting til the share button available
            timeout=100000  # 100秒超时
        )

        markdown_divs = await page.wait_for_selector('.markdown')

        # 获取第二个元素的文本内容（不包含 HTML 标签）
        article = await markdown_divs.inner_text()

        dict_final = {'runStatus': 1, 'article': article}
        list_ = []

        element = await page.wait_for_selector(
            '.flex-row-reverse',  # waiting til the share button available
            timeout=100000  # 100秒超时
        )
        if element:
            await element.click()
            # 3. 5秒内等待 div.dc433409 加载，超时则抛TimeoutError
            target_div = await page.wait_for_selector(
                selector='[slot="content"] ul',  # 目标元素选择器
                timeout=5000  # 超时时间：5000毫秒（5秒）
            )
            # target_div.wait_for_element_state(state="visible")
            # 定位目标div下所有 <a> 标签（即包含链接和标题的标签）
            a_tags = await target_div.query_selector_all("li a")

            await asyncio.sleep(1)
            # page.screenshot(path="full_page.png", full_page=True)

            # 遍历a标签，提取链接和标题
            for a_tag in a_tags:
                # 提取链接：a标签的href属性
                url = await a_tag.get_attribute("href")
                # 提取标题：a标签内 class="search-view-card__title" 的div文本（标题容器）
                title_elem = await a_tag.query_selector(".break-words")  # 定位标题元素
                if title_elem:
                    title = await title_elem.text_content()
                    title = title.strip()
                else:
                    title = "无标题"


                source_elem = await a_tag.query_selector(".text-xs")  # 定位标题元素
                if source_elem:
                    source = await source_elem.text_content()
                    source = source.strip()
                else:
                    source = "无来源"

                dict_ = {'title': title, 'url': url, 'source': source}
                list_.append(dict_)
            dict_final['list'] = list_

        await page.click('[aria-label="Share"]')
        await page.click('button.relative .pointer-events-none')

        for i in range(1, 5):
            if self.share_id:
                break
            else:
                await asyncio.sleep(i)

        if self.share_id:
            share_link = f'https://chatgpt.com/share/{self.share_id}'
            dict_final['share_link'] = share_link


        return  dict_final

    async def run_once(self, question: str) -> dict:
        if not self.inited:
            await self.create_playwright()
            self.inited = True

        if len(self.context.pages) > 0:
            page = await self.context.pages[0]
        else:
            page = await self.context.new_page()

        try:
            await page.goto("https://chatgpt.com/")
            page.on("response", self.handle_response)  # Register the handler
            return await self.handle_data(page, question)
        finally:
            await page.close()

async def main():
    q = "给出2025年9月22号，食品安全相关的负面新闻有哪些，给出标题和链接。"
    cg = ChatGpt()
    rs = await cg.run_once(q)
    print(rs)

if __name__ == '__main__':
    asyncio.run(main())