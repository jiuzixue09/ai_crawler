
import json
import os
import random
import re
from datetime import datetime
from uuid import uuid1

import requests
from playwright.async_api import Page

# 隧道域名:端口号
tunnel = "f679.kdltps.com:15818"

# 用户名密码方式
username = "t12187413243075"
password = "yr4fjfks"

proxies = {
    "http": "http://%(user)s:%(pwd)s@%(proxy)s/" % {"user": username, "pwd": password, "proxy": tunnel},
    "https": "http://%(user)s:%(pwd)s@%(proxy)s/" % {"user": username, "pwd": password, "proxy": tunnel}
}

user_agent = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.0.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0',
    ]
headless = True

def get_random_user_agent():
    return user_agent[random.randrange(len(user_agent))]


def local_ip():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 1))  # connect() for UDP doesn't send packets
    local_ip_address = s.getsockname()[0]
    return local_ip_address


async def image_save_as(page: Page, screenshot_dir=os.path.join(os.getcwd(), 'screenshot')):
    p = os.path.join(screenshot_dir, datetime.now().strftime('%Y-%m-%d'))
    os.makedirs(p, exist_ok=True)
    file_name = uuid1().hex + '.png'
    full_path = os.path.join(p,file_name)
    await page.screenshot(path= full_path, full_page=True)
    return full_path

def public_ip():
    try:
        resp = requests.get('https://ipinfo.io/ip', timeout=5)
        ip = resp.content.decode('utf-8')
    except:
        resp = requests.get('http://myip.ipip.net', timeout=5)
        ip = str.join('', re.findall('[0-9.]{4}', resp.content.decode('utf-8')))
    return ip


def save_cookies(context,path_name):
    cookies = context.cookies()
    cookies = {"cookies":cookies}
    with open(path_name, "w") as f:
        f.write(json.dumps(cookies))


def find_key_in_json(obj, target_key, found_values=None):
    """
    Recursively searches for a target_key in a nested JSON-like object
    (Python dictionary or list) and returns a list of all found values.
    """
    if found_values is None:
        found_values = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == target_key:
                found_values.append(value)
            # Recursively search in nested dictionaries and lists
            if isinstance(value, (dict, list)):
                find_key_in_json(value, target_key, found_values)
    elif isinstance(obj, list):
        for item in obj:
            # Recursively search in items within the list
            if isinstance(item, (dict, list)):
                find_key_in_json(item, target_key, found_values)
    return found_values

async def select_drop_down_item(page: Page, button_class_name, class_name=None, text_name=None):

    button = await page.wait_for_selector(button_class_name,timeout=5000)
    content = await button.text_content()
    if text_name not in content.strip():
        await button.click()

        button = page.locator(class_name,has_text=text_name)
        await button.wait_for(state="visible")
        await button.click()