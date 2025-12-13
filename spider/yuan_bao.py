import asyncio

from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from util import crawler_util


class YuanBao:
    def cleanup_function(self):
        self.context.close()
        self.playwright.stop()

    async def create_playwright(self):
        playwright = await async_playwright().start()

        storage_state = "cookies/yuanbao/yuanbao_1.json"

        browser = await playwright.chromium.launch(headless=crawler_util.headless)
        context = await browser.new_context(storage_state=storage_state,
                                            user_agent=crawler_util.get_random_user_agent())

        await Stealth().apply_stealth_async(context)

        self.context = context
        self.playwright = playwright


    def __init__(self):
        self.context = None
        self.playwright = None
        self.share_id = None
        self.inited = False


    async def handle_response(self,response):
        # https://yuanbao.tencent.com/api/conversations/v2/share
        if "api/conversations/v2/share" in response.url and response.status == 200:
            print(f"Intercepted API response: {response.url}")
            try:
                res = await response.json()
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
                raise e
                print(e)

    async def run_once(self, question: str) -> dict:
        if not self.inited:
            await self.create_playwright()
            self.inited = True

        async with await self.context.new_page() as page:
            try:
                await page.goto("https://yuanbao.tencent.com/")

                page.on("response", self.handle_response)  # Register the handler
                page.on("dialog", lambda dialog: dialog.accept())
                return await self.handle_data(page, question)
            except Exception as e:
                raise e
                print(e)



    async def handle_data(self, page, question: str) -> dict:

        model_name = 'DeepSeek'
        deep_think = True
        internet_search = True
        internet_search_name = 'Auto'

        await crawler_util.select_drop_down_item(page,
                                                         '[dt-button-id="model_switch"]',
                                                         'div.drop-down-item__name',
                                                 model_name)

        if deep_think :
            deep_think_button = await page.wait_for_selector('[dt-button-id="deep_think"]', timeout=10000)
            class_name = await deep_think_button.get_attribute("class")
            if 'checked' not in class_name.strip():
                await deep_think_button.click()

        if internet_search:
            online_search_button = await page.wait_for_selector('[dt-button-id="internet_search"]', timeout=10000)
            await online_search_button.click()

        if await page.locator('div.yb-switch-internet-search-btn__right').is_visible():
            await crawler_util.select_drop_down_item(page,
                                               'div.yb-switch-internet-search-btn__right',
                                               'div.drop-down-item__name',
                                                     internet_search_name)

        textarea = page.locator('div.ql-editor')
        await textarea.fill(question)

        await page.wait_for_timeout(100)
        await page.locator("#yuanbao-send-btn").click()

        share_button = await page.wait_for_selector('.agent-chat__toolbar_new .agent-chat__toolbar__share', timeout=100 * 1000)

        markdown_divs = page.locator('div.hyc-component-reasoner__text')
        if not await markdown_divs.is_visible():
            markdown_divs = page.locator('.hyc-component-deepsearch-cot > .hyc-content-md-done')

        # 获取第二个元素的文本内容（不包含 HTML 标签）
        article = await markdown_divs.inner_text()

        dict_final = {'runStatus': 1, 'article': article}
        list_ = []

        element = page.locator(".agent-chat__search-guid-tool__source")
        try:
            await element.wait_for(state='visible', timeout=60 * 1000) #这行代码主要是让程序休眠时间一段时间，防止账号被封
        except Exception as e:
            print(e)

        if element and await element.is_visible():
            await element.click()
            # 3. 5秒内等待 div.dc433409 加载，超时则抛TimeoutError
            target_div = await page.wait_for_selector(
                selector='[id="chatReferenceList"] ul',  # 目标元素选择器
                timeout=5000  # 超时时间：5000毫秒（5秒）
            )

            # page.screenshot(path="full_page.png", full_page=True)

            # 定位目标div下所有 <a> 标签（即包含链接和标题的标签）
            a_tags = await target_div.query_selector_all("li")

            # 遍历a标签，提取链接和标题
            for a_tag in a_tags:
                # 提取链接：a标签的href属性
                url = await a_tag.get_attribute("dt-ext6")
                # 提取标题：a标签内 class="search-view-card__title" 的div文本（标题容器）
                title_elem = await a_tag.query_selector(".hyc-common-markdown__ref_card-title")  # 定位标题元素

                if title_elem:
                    title = await title_elem.text_content()
                    title = title.strip()
                else:
                    title = '无标题'

                source_elem = await a_tag.query_selector(".hyc-common-markdown__ref_card-foot__txt")  # 定位来源元素
                if source_elem:
                    source = await source_elem.text_content()
                    source = source.strip()
                else:
                    source = '无来源'

                dict_ = {'title': title, 'url': url, 'source': source}
                list_.append(dict_)
                dict_final['list'] = list_

        await share_button.click()
        copy_button = await page.wait_for_selector(
            '.agent-chat__share-bar__content__center .agent-chat__share-bar__item__logo:first-child')

        for i in range(1, 5):
            if self.share_id:
                break
            else:
                await asyncio.sleep(i)
                await copy_button.click()

        if self.share_id:
            share_link = f'https://yb.tencent.com/s/{self.share_id}'
            dict_final['share_link'] = share_link

        return dict_final


async def main():
    crawler_util.headless = False
    yb = YuanBao()

    q = "上海现在换电车还有什么官方补贴？"
    rs = await yb.run_once(q)
    print(rs)

if __name__ == '__main__':
    asyncio.run(main())