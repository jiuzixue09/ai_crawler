import re
from playwright.sync_api import Playwright, sync_playwright, expect
import time


def ini_button(page, name):
    button = page.get_by_role(
        "button",
        name=name,  # 匹配按钮内的文本
        exact=True  # 精确匹配文本，避免模糊匹配其他按钮
    )
    button.wait_for(state="visible")
    is_state = button.evaluate("el => el.classList.contains('_76f196b')")
    if not is_state:
        button.click()

def run_once(playwright: Playwright, question: str) -> dict:
    browser = playwright.chromium.launch(headless=False)
    # context = browser.new_context()
    context = browser.new_context(storage_state="cookies/deepseek/deepseek.json")
    page = context.new_page()
    page.goto("https://chat.deepseek.com/")
    # page.wait_for_timeout(2000)
    # ini_button(page, "深度思考")
    ini_button(page, "DeepThink")
    # ini_button(page, "联网搜索")
    ini_button(page, "Search")
    textarea = page.locator('textarea.ds-scroll-area')
    textarea.fill(question)

    page.wait_for_timeout(100)
    page.get_by_role("button").nth(4).click()

    # 等待元素加载，设置超时时间为100秒(100000毫秒)
    share_element = page.wait_for_selector(
        "div.ds-flex > div.ds-flex > div.ds-icon-button:last-child", # waiting til the share button available
        timeout=100000  # 100秒超时
    )
    # ds-icon-button _7436101 bcc55ca1 ds-icon-button--disabled
    markdown_divs = page.locator('div[class="ds-markdown"]')

    # 可选：等待第二个元素加载完成（确保元素存在）
    markdown_divs.nth(1).wait_for()

    # 获取第二个元素的文本内容（不包含 HTML 标签）
    article = markdown_divs.nth(1).inner_text()

    dict_final = {}
    dict_final['status']  = '0'
    dict_final['article'] = article
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

    #share link from api https://chat.deepseek.com/api/v0/share/create
    share_element.click()
    page.wait_for_selector(".ds-basic-button--primary").click(timeout=2000)
    page.wait_for_selector(".ds-modal-content__footer button").click(timeout=2000)
    time.sleep(1)
    share_link = page.query_selector('.ds-modal-content__footer span').text_content().strip()
    dict_final['list'] = list_
    dict_final['share_link'] = share_link

    return  dict_final

if __name__ == '__main__':
    with sync_playwright() as playwright:
        question = "消费者对智能驾驶系统的信任度如何建立？"
        # question = "消费者对新能源汽车的续航焦虑如何缓解？"
        dict_final = run_once(playwright, question)
        print(dict_final)