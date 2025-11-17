import json

from playwright.sync_api import Page


def zoom_in(page, times=1):
    for _ in range(times):
        page.keyboard.down("Control")
        page.keyboard.press("-")
        page.keyboard.up("Control")


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

def select_drop_down_item(page: Page, button_class_name, class_name=None, text_name=None):

    button = page.wait_for_selector(button_class_name,timeout=5000)
    if text_name not in button.text_content().strip():
        button.click()

        button = page.locator(class_name,has_text=text_name)
        button.wait_for(state="visible")
        button.click()