import re
import time

from playwright.sync_api import Playwright, sync_playwright, expect
import crawler_util

share_id = None

def handle_response(response):
    global share_id
    # https://www.doubao.com/samantha/thread/share/
    if "samantha/thread/share/" in response.url and response.status == 200 :
        print(f"Intercepted API response: {response.url}")
        try:
            res = response.json()
            if res:
                data = res['data']
                if data and 'pre_share_id' in data:
                    share_id = data['pre_share_id']
                elif data and 'share_id' in data:
                    share_id = data['share_id']
        except Exception as e:
            print(e)


def data_append(page, list_):

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
        dict_ = {'title': title, 'url': url}
        list_.append(dict_)



def run_once(playwright: Playwright, question: str) -> dict:
    browser = playwright.chromium.launch(headless=False)
    # context = browser.new_context()
    context = browser.new_context(storage_state="cookies/doubao/doubao.json")
    page = context.new_page()
    page.goto("https://www.doubao.com/chat/")
    page.on("response", handle_response)  # Register the handler
    deep_thinking_button = page.wait_for_selector('[data-testid="use-deep-thinking-switch-btn"] > button',timeout=8000)

    deep_thinking_button.click()

    textarea = page.locator('textarea.semi-input-textarea')
    textarea.fill(question)

    page.wait_for_timeout(100)
    page.locator("#flow-end-msg-send").click()

    # 等待分享元素加载，设置超时时间为100秒(100000毫秒)
    share_element = page.wait_for_selector(
        'div.message-action-button-main [data-testid="message_action_share"]', # waiting til the share button available
        timeout=100000,  # 100秒超时
        state='visible'
    )
    dict_final = {'status':0 , 'article':''}

    list_ = []

    nodes = page.query_selector_all(
        '[data-testid="receive_message"] [data-testid="message_content"] > div > [data-render-engine="node"]')
    node_size = len(nodes)
    receive_message = nodes[node_size - 2].wait_for_selector(' > [data-testid="message_text_content"].flow-markdown-body')

    # 获取文本内容（不包含 HTML 标签）
    article = receive_message.inner_text()
    reference_element = nodes[node_size - 1].query_selector('[data-testid="search-reference-ui"]')

    try:
        reference_element.click(timeout=1000)
        data_append(page, list_)
    except Exception as e:
        print(e)

    page.screenshot(path="full_page.png", full_page=True)
    share_element.click(timeout=1000)
    page.wait_for_selector('[data-testid="thread_share_copy_btn"]')
    for e in page.query_selector_all('[data-testid="thread_share_copy_btn"]'):
        try:
            e.click(timeout=1000)
        except Exception as e:
            print(e)

    for i in range(1, 5):
        if share_id:
            break
        else:
            time.sleep(i)

    # page.wait_for_selector('.pointer-events-auto [data-testid="thread_share_copy_btn"]').click()

    # # 展开深度思考结果
    # page.wait_for_selector('[data-testid="collapse_button"]', timeout=10000).click()
    # markdowns = page.wait_for_selector('//div[contains(@class,"think-block-container")]').query_selector_all(' > div')
    # while markdowns:
    #     markdown = markdowns.pop(0)
    #     content = markdown.query_selector('[data-testid="message_text_content"]')
    #     reference_ui =  markdown.query_selector('[data-testid="search-reference-ui"]')
    #     if content:
    #         if article:
    #             article += '\n##################################\n'
    #         article += content.inner_text()
    #     if reference_ui:
    #         reference_ui.click()
    #         data_append(page, list_)

    if share_id:
        share_link = f'https://www.doubao.com/thread/{share_id}'
        dict_final['share_link'] = share_link

    dict_final['article'] = article
    dict_final['list'] = list_
    return  dict_final

if __name__ == '__main__':

    with sync_playwright() as playwright:
        question = "新能源汽车渗透率如何突破50%瓶颈？"
        rs = run_once(playwright, question)
        print(rs)