import json
import os
import random
import time

from playwright.sync_api import sync_playwright

import bai_du
import chart_gpt
import deepseek
import dou_bao
import excel_util
import logging_config
import yuan_bao


logging = logging_config.setup_logger('crawler.log','geomonitor')

def select_item_from_console(items):
    """Display items and let user select by index."""
    for i, item in enumerate(items):
        print(f"{i}: {item}")

    while True:
        try:
            choice = int(input("Select an website by index: "))
            if 0 <= choice < len(items):
                return items[choice]
            print("Invalid index. Try again.")
        except ValueError:
            print("Please enter a valid number.")


def input_and_out_handle():
    # Get file path from user
    file_path = input("Enter the file path to read: ").strip()
    if '/' not in file_path:
        file_path = os.path.join(os.getcwd(), file_path)

    # Check if file exists
    if not os.path.exists(file_path):
        print("File not found!")
        return

    # Get output directory
    output_dir = input("Enter the output directory: ").strip()
    if '/' not in output_dir:
        output_dir = os.path.join(os.getcwd(), output_dir)

    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Get output filename
    output_name = input("Enter the output Excel filename (without extension): ").strip()
    output_path = os.path.join(output_dir, f"{output_name}.xlsx")

    items = ['baidu', 'deepseek', 'doubao', 'yuanbao', 'chartgpt', 'all']

    selected = select_item_from_console(items)

    return file_path, output_path, selected


def handle():
    site_map = {'baidu': bai_du, 'deepseek': deepseek, 'doubao': dou_bao, 'yuanbao': yuan_bao,
                'chartgpt': chart_gpt}

    file_path, output_path, selected = input_and_out_handle()

    if selected == 'all':
        site_crawlers = [bai_du, deepseek, dou_bao, yuan_bao]
    else:
        site_crawlers = [site_map.get(selected)]

    eu = excel_util.ExcelUtil()
    # eu = excel_util.ExcelUtil('rs.xlsx')
    # data = ['问题', '回答', '分享链接', '来源信息']
    # eu.append_excel(data)

    with open(file_path, 'r') as file:
        for l in file:
            question = l.strip()
            logging.info(question)

            for site_crawler in site_crawlers:
                data = search(question, site_crawler)

                try:
                    eu.append_excel(data)
                    eu.save_excel(output_path)
                except Exception as e:
                    logging.error(e)


def search(question, site_crawler):
    with sync_playwright() as playwright:
        try:

            data_json = site_crawler.run_once(playwright, question)
            data = [question, data_json['article'], data_json['share_link'], str(data_json.get('list', ''))]
            logging.info(json.dumps(data))
            return data
        except Exception as e:
            logging.error(e)
            return None



if __name__ == '__main__':
    handle()
