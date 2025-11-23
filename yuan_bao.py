import re
import time

from playwright.sync_api import Playwright, sync_playwright, expect
import crawler_util


share_id = None

def ini_button(page, css_class):
    button = page.wait_for_selector(
        selector=css_class,
        timeout=5000  # 超时时间：5000毫秒（5秒）
    )
    button.click()

def handle_response(response):
    global share_id
    #https://yuanbao.tencent.com/api/conversations/v2/share
    if "api/conversations/v2/share" in response.url and response.status == 200 :
        print(f"Intercepted API response: {response.url}")
        try:
            res = response.json()
            if res:
                if 'shareId' in res:
                    share_id = res['shareId']
                else:
                    data = res['data']
                    if data and 'pre_share_id' in data:
                        share_id = data['pre_share_id']
                    if data and 'share_id' in data:
                        share_id = data['share_id']
        except Exception as e:
            print(e)

def run_once(playwright: Playwright, question: str) -> None:
    global share_id
    browser = playwright.chromium.launch(headless=False)
    # context = browser.new_context()
    context = browser.new_context(storage_state="cookies/yuanbao/yuanbao_1.json")
    page = context.new_page()
    page.goto("https://yuanbao.tencent.com/")
    page.on("response", handle_response)  # Register the handler
    page.on("dialog", lambda dialog: dialog.accept())

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

    # 等待元素加载，设置超时时间为100秒(100000毫秒)
    element = page.wait_for_selector(
        ".agent-chat__search-guid-tool__source", # waiting til the share button available
        timeout=100000  # 100秒超时
    )
    # ds-icon-button _7436101 bcc55ca1 ds-icon-button--disabled
    markdown_divs = page.locator('div.hyc-component-reasoner__text')

    # 获取第二个元素的文本内容（不包含 HTML 标签）
    article = markdown_divs.inner_text()

    dict_final = {}
    dict_final['status']  = '0'
    dict_final['article'] = article
    list_ = []

    if element:
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

        page.wait_for_selector('.agent-chat__toolbar_new .agent-chat__toolbar__share').click()
        copy_button = page.wait_for_selector('.agent-chat__share-bar__content__center .agent-chat__share-bar__item__logo:first-child')

        for i in range(1, 5):
            if share_id:
                break
            else:
                time.sleep(i)
                copy_button.click()

    if share_id:
        share_link = f'https://yb.tencent.com/s/{share_id}'
        dict_final['share_link'] = share_link

    return  dict_final

if __name__ == '__main__':

    with sync_playwright() as playwright:
        question = "给出2025年9月22号，食品安全相关的负面新闻有哪些，给出标题和链接。"
        dict_final = run_once(playwright, question)
        print(dict_final)