import json
import sys

from playwright.sync_api import sync_playwright

import bai_du
import chart_gpt
import deepseek
import dou_bao
import excel_util
import logging_config
import yuan_bao


logging = logging_config.setup_logger('crawler.log','geomonitor')


def handle(file_path, output_path, selected):
    site_map = {'baidu': bai_du, 'deepseek': deepseek, 'doubao': dou_bao, 'yuanbao': yuan_bao,
                'chartgpt': chart_gpt}


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
    args = sys.argv
    handle(args[1], args[2], args[3])