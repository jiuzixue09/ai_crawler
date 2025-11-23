import time

from playwright.sync_api import Playwright, sync_playwright
import crawler_util

share_id = None

def handle_response(response):
    global share_id
    #https://chatgpt.com/backend-api/share/post
    #https://chatgpt.com/backend-api/share/create
    #https://chatgpt.com/s/t_691edd5140b88191a60d1d0833fb4c8c
    if "/share/create" in response.url and response.status == 200 :
        print(f"Intercepted API response: {response.url}")
        try:
            res = response.json()
            # print(res)
            if res:
                if 'share_id' in res:
                    share_id = res['share_id']
                else:
                    data = res['post']
                    if data and 'id' in data:
                        share_id = data['id']
        except Exception as e:
            print(e)


def run_once(playwright: Playwright, question: str) -> None:
    global share_id
    # browser = playwright.chromium.launch(headless=False)
    # context = browser.new_context()

    # cookies_to_set = [
    #     {
    #         "name": "__Secure-next-auth.session-token",
    #         "value": 'eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..rj63KbLRxFHhPWEM.ZoOUJbz6p1AwWPF4njnc7inTi0JgQaEnF6UQIVd5oNEF32fmJIpEQCzdZWzR3tvqWJaR261U1ht6a1tjA0zZdEUqcEVSeVk5av0IqoL7XgLW3xnqnYYJ5pbdqEQ_8lXN6QEz_P5YZyLE6wgD1sYdHjQYmIS0uSX4ECeTZAL_7rDfwcXcLNwOPGqsxHMhn5EeTBbWYT8MlWngYsZhbIp85U-ZQ7u18dQa-mJ97NrLW3esVCkMV2XVDdItbyUK4tNlq4lT7emx-b-XpPUCHPyL2rz_GjBCPkq4LSLnMvYIjweMsTvS6A42RxFkodM2HTptLaGF0zI-Pw5rANLUjU2byLNu1795HH3Ca1vS4cczsmXzSuC91u_qkp8QgxExF42CTp88dqs19cai3oZGiRaxs7_DGHkuvii3VD8MGSR0h-Cqp1iklyMthXPtz76VLKb4_Qy-602gSkcVaC49JhTn_j1pbq-Rq2QkhS1Y6593-df2tDYhjHQUfgbH-ACBADAAcNbwfGKcm8nXePiK3zSoZJNFOexT9ZUOuleTQlbxrLxZwzmnvO9Q1kpVr-16DhtTP5A5sXUiCI4JtcxZSSiUb0tPmwV6Gh93n_nNLdXhzMWtefcw97lO5OMU8yFLH4EqvLD9OJ9VPkU0_LwRpt9BdG9-BBJGUg2pLK1F0oE9vqJ-XPZKCuBgSe1Ik-vvXvZ_SCBGY2ASjCor2tNlTONjStc-zlYAsic89iVUJXktVQSn9yfYgEOX8aSElPsZQfLBtbpYbsuaCECVkvndstzLIUtwEEh4uP7sNpcQExirOmVyPeZDT0tayPFIB1T90hbc1-sNQXAVZmDCj3fyAcdU-KpmH5GLr8lR2g6fZHh5p9XTIi08vm6rAVs8hZZGBU0vcmbDONJQ0bg-oSnrhyZa3K1E-yNChz-TNkE6iSUJMx_jBfXi_BFF03AHQIqzFfgK4k9t0AXi9INrsaG_J0g5oAQRQFDr6GoRJObH0ZpnhVJEnTeLsAXnpggXL60oZKbgaz6sbXb5pzJBYeFNKxZMOY6P-CxeH2_bwj8-MUp1PIk0SLqnA5avFLQseazaCWkpRuMvbc7-UwNE84PRnjlTaNFcAeD-2DEklwHKIIVqdr9poCgsuErsgEr7ZQDa5vC--6KEIZ1Uuz4tOszPGBMvwLtxBaVzxXXgMZAFLDvBqrv_8I19Dda6j8-nWLXRqQJDBuLSoZZMSfk4txU_51KK4rzRUNbyJoJ89V56Tt8iqmJfTxSulTvZpUJ1KPVHD1HadA_S-_65y8p0V9FlzMuIEV3MK2YuGBra0-zFXNX2REMojmeB-fmesotoNK2xKIxMQxOXkR8ziXO-OKFiKY06h1jERooZgJbgyta1HSh4BmUdmjwK51vXIyMHe5A9gXP-l5nLXgsuQrM3RULhusiVZ_7iYWqWbpLv8iKZN8xgqUQg25Jp0_QYfgVBX4Km9ki5Vmmzm1m4T6-lORKSmTS1aOvz1cNxBlBoCevWz-e9crTxEdxqT6FJtZbb-sWeYXbovS6IyelZIcJnoXwbwZanbFfkchN4APjAh2s4uaGNwT8q1KL1uMj6Q8S98nXRazOg2j6dZaRqnESNItaqJAJX2Oy1hGsnKy3yG6sDT38gXePiQtBkAHDsTJcWTCYzXLOT5EZ94ytbE4ugJhYCEy8n3dPfsHzghS_8k3nIK2Gw8S8eCpxO1C7j9qL7gvwGS7HUn7ejnm1kIfV5uq5VSppbm45mv9BC9F183MBNZPU2h9OwgfALOk8bIixGQf0WQUIPpmkO5X52Lf8faOQgyZVRWGxNwAD846X0It_i9Fr5bZgMRwWqInhxZIwgFTXrq8Du4DwUHucUsYlfeB3oilLf-6pB-arWCssrOqTC_xX4zf6v6W7Bkdu5fYcgObJCYewrtzeyDFi-mOjSSpdcO0OJZdJNlTZZYmKo8ETta6Qb36myC4ArVICzZnLFbQmbAK_KXB7JLamssetFjwj5zCLffpKBCBB53cYRNoWllILa9a0Q-dajBcGhZ-xwpCo6xfHXS2JqG4C-HXWP0-wqk1j_D8Drl-h_rJVPPjTOm1zCmLosg-WQJahhoPKfygwZ9YfgWnW0srfUzKYmTEcKjLr-RMQgKwmXaDA6C8aBvYBR0-xRyWLYYpNDl1Kiqwb0ZiWmSLasJXMoEk6kRC80or6pKW-IxDDcbI4a-3BEYVRa0-hiLJm9dGKuV-SlTMHELJ3He_iiUh4_mQfVf_bWGZoPV4VldqotFrt-L3cnUnzld1p1Wo-G2sUs9ECzr6PBaC3Q5VkK1B4XaFciB-kETwLY8RJf4q8aZs0mH8OcsWvJ-Vw7vaE1d-jKpo3GP4hINQTe-LyeKs8NJ_HEwjXU38SiLJGDxWhr57rPyImpMBsWIZm26XKRfIF9jMqhvHSQ-HhFY_Y6n7cRcIm5eiNuYRMBRdE5SykJkRYplGecLN_mn_EUsckhxS09MRMaB4qcuD67BpKLortw37mBLQYX6Clu9zq0mpWnmxKBpu4RW93pHhHMf35qX8eraz_pwrY1PpnEh5A3XpYFQ9ZFo78v2zLiXEXcWmGOUHYv6Dtzl4V0h2TY3nqMf3MJktQCPYBBiwdHOLKxy8K5AsN-KP-GMv6o11gpKxvrmKlui-55U0THU-ry8plIaCKRRfWBTn03ZNUankZdrwx9W9adgTH6-kM36dqm6dXZAFu9cQhfiADTyO0twSUSPuRUxDR710J7XMVDWcKEfA0Lz3An-ARKiHcp3Fyp3AmxaXQAjplUtv8qPok8505oIBg9rzTM8jTqbjzQ2nFbcO__oUCY0h-n5ixaScgWTbfSLpKp9kwGMKGLQyml8vKF_OL_HsDKkQebsDU4hGs4IVfoRHfTTRvBuzMk7038DXbOOfuv8egxK6X-DKBDTKvcSZ5JRLeM8shu9UG8xvPshaij6CiI8AoQlzyODsaaFCecj8OmVO1Et7loKVZ-sikUDJjSGBmCxhsTdgbxvlfyA8ctvguvqZuL8WQ8nB68j7njZfTvvSceOgzW_rwEccUOrfwAGMctCx6B71aJgtk2RVjQMZg_kezHJ-V7cEzXqGRFyDoRMi-SypVUcCJxSVE9kAKrE3NthpE2uj6OW4tjzpQtbe0YzMUW5DlIMJcckfPyndm8YuA7GHTeNDccSa5nBfXaQ0mzqzx49m9lvzwLKGZZ3Qp9w4nKynkdzFfDuW3aCwN90P0j_FxL3IIU8AX5_ot3V8a08TPCwSS7mNfK6sOsQA_U-nvJCtvwr6xQub7NrQrZ-RjqWhKsaue4GxFttHpIpXCVNrdD1ZJ4iHr2HuOgsIckdwe7z07U-0XLjuekITLE_LgXlEdhNnIdKq3Dcs40BWzg3pIFCNTPUqlWlL-9tOL4zRul7n9TMvAm3cVFfzDAhtracCTG1UTQgmpwA-JP18ySdLccWSyjktv_HaKX34e0G10X5VE9Wvxb8MiHzSjedQNMQYT3MODTyE0RzRvfaNJDSi1VEkhPNL__x-wF0q2NaC8HA-Tlfx7O7ZY-8c2MdbuUverQAlx2dmKCKw1Do1o3t2_e-emNLDUOCz4IThDlvHt4KmlCV2VUfOyXR7hXTVpMNmI6pU1QM8erzLBCLg.e42uCDGff890L8eIfQnx2g',
    #         "domain": ".chatgpt.com",  # Replace with the target domain
    #         "path": "/",
    #         "expires": -1,  # Optional: -1 for session cookie, or a Unix timestamp for expiration
    #         "httpOnly": True,  # Optional: True or False
    #         "secure": True,  # Optional: True or False
    #         "sameSite": "Lax"  # Optional: "Strict", "Lax", or "None"
    #     }
    # ]
    # context.add_cookies(cookies_to_set)
    # /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir=foo
    browser = playwright.chromium.connect_over_cdp("http://127.0.0.1:9222")
    browser.new_context(storage_state="cookies/chatgpt/chatgpt.json")
    default_context = browser.contexts[0]
    if len(default_context.pages) > 0:
        page = default_context.pages[0]
    else:
        page = default_context.new_page()

    # context = browser.new_context(storage_state="chatgpt.json")
    # page = context.new_page()
    # stealth_sync(page)
    page.goto("https://chatgpt.com/")
    page.on("response", handle_response)  # Register the handler

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
            dict_ = {}
            dict_['title'] = title
            dict_['url'] = url
            list_.append(dict_)
        dict_final['list'] = list_

    page.wait_for_selector('[aria-label="Share"]').click()
    page.wait_for_selector('button.relative .pointer-events-none').click()

    for i in range(1, 5):
        if share_id:
            break
        else:
            time.sleep(i)

    if share_id:
        share_link = f'https://chatgpt.com/share/{share_id}'
        dict_final['share_link'] = share_link


    return  dict_final

if __name__ == '__main__':

    with sync_playwright() as playwright:
        question = "给出2025年9月22号，食品安全相关的负面新闻有哪些，给出标题和链接。"
        dict_final = run_once(playwright, question)
        print(dict_final)