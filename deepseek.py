import asyncio

from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import crawler_util

class DeepSeek:

    def cleanup_function(self):
        self.context.close()
        self.playwright.stop()

    def __init__(self):
        self.inited = False
        self.context = None
        self.playwright = None


    async def create_playwright(self):
        storage_state = "cookies/deepseek/deepseek.json"
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=crawler_util.headless)
        context = await browser.new_context(storage_state=storage_state,
                                            user_agent=crawler_util.get_random_user_agent())

        await Stealth().apply_stealth_async(context)

        self.context = context
        self.playwright = playwright


    async def handle_data(self,page, question: str) -> dict:
        buttons = await page.query_selector_all('button')

        for b in buttons:
            await b.wait_for_element_state(state='visible')
            t = await b.text_content()
            if t.strip() in ['DeepThink','深度思考','Search','联网搜索']:
                await b.click()

        textarea = page.locator('textarea.ds-scroll-area')
        await textarea.fill(question)

        await page.wait_for_timeout(100)
        await page.get_by_role("button").nth(4).click()

        # 等待元素加载，设置超时时间为100秒(100000毫秒)
        share_element = await page.wait_for_selector(
            "div.ds-flex > div.ds-flex > div.ds-icon-button:last-child",  # waiting til the share button available
            timeout=100000  # 100秒超时
        )
        # ds-icon-button _7436101 bcc55ca1 ds-icon-button--disabled
        markdown_divs = await page.query_selector_all('.ds-message .ds-markdown')

        article = await markdown_divs.pop().inner_text()

        dict_final = {'status': '0', 'article': article}
        list_ = []
        source_element = page.locator(
            "div.ds-scroll-area div.ds-message > div > div:has(.site_logo_back)"
        )

        if source_element and await source_element.last.is_visible():
            try:
                await source_element.last.click()
                target_div = await page.wait_for_selector(
                    selector="div.scrollable div.ds-scroll-area",  # 目标元素选择器
                    timeout=5000  # 超时时间：5000毫秒（5秒）
                )

                # page.screenshot(path="full_page.png", full_page=True)

                # 定位目标div下所有 <a> 标签（即包含链接和标题的标签）
                a_tags = await target_div.query_selector_all("div a")  # 仅查询该div内部的a标签

                # 遍历a标签，提取链接和标题
                for a_tag in a_tags:
                    # 提取链接：a标签的href属性
                    url = await a_tag.get_attribute("href")
                    title_elem = await a_tag.query_selector("div.search-view-card__title")  # 定位标题元素
                    if title_elem:
                        title = await title_elem.text_content()
                        title = title.strip()
                    else:
                        title = "无标题"

                    source_elem = await a_tag.query_selector('.site_logo_back + span')
                    if source_elem:
                        source = await source_elem.text_content()
                        source = source.strip()
                    else:
                        source = "无来源"

                    dict_ = {'title': title, 'url': url, 'source': source}
                    list_.append(dict_)
            except Exception as e:
                print(e)

        # share link from api https://chat.deepseek.com/api/v0/share/create
        await share_element.click()
        await page.click(".ds-basic-button--primary",timeout=2000)
        await page.click(".ds-modal-content__footer button",timeout=2000)
        await asyncio.sleep(1)

        share_button = await page.query_selector('.ds-modal-content__footer span')
        share_link = await share_button.text_content()

        dict_final['list'] = list_
        dict_final['share_link'] = share_link.strip()

        return dict_final

    async def run_once(self, question: str) -> dict:
        if not self.inited:
            await self.create_playwright()
            self.inited = True

        async with await self.context.new_page() as page:
            await page.goto("https://chat.deepseek.com/")
            return await self.handle_data(page, question)



async def main():
    crawler_util.headless = False
    # question = " 汽车元宇宙概念的落地场景？"
    q = "今年成都上牌补贴是多少钱？"
    ds = DeepSeek()
    rs = await ds.run_once(q)
    print(rs)

if __name__ == '__main__':
    asyncio.run(main())