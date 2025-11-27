import json
import os
import sys

import bai_du
import chat_gpt
import crawler_util
import deepseek
import dou_bao
import excel_util
import logging_config
import yuan_bao



def handle(file_path, output_path, selected):
    site_map = {'baidu': bai_du.BaiDu, 'deepseek': deepseek.DeepSeek, 'doubao': dou_bao.DouBao, 'yuanbao': yuan_bao.YuanBao,
                'chartgpt': chat_gpt.ChatGpt}


    if selected == 'all':
        site_crawlers = [bai_du.BaiDu, deepseek.DeepSeek, dou_bao.DouBao, chat_gpt.ChatGpt, yuan_bao.YuanBao]
    else:
        site_crawlers = [site_map.get(selected)]

    questions = []
    with open(file_path, 'r') as file:
        for l in file:
            questions.append(l)

    threads = []
    for site_crawler in site_crawlers:
        op = os.path.join(output_path,site_crawler.__name__ + '.xlsx')
        search(questions, op, site_crawler())
        # t = Thread(target= search, args=(questions, op, site_crawler()))
        # t.start()
        # threads.append(t)

    # wait_for_threads(threads)


def wait_for_threads(threads):
    for t in threads:
        t.join()


def search(questions, output_path, site_crawler):
    eu = excel_util.ExcelUtil()
    for question in questions:
        try:
            data_json = site_crawler.run_once(question)
            data = [question, data_json['article'], data_json['share_link'], str(data_json.get('list', ''))]
            logging.info(json.dumps(data))

            eu.append_excel(data)
            eu.save_excel(output_path)

        except Exception as e:
            logging.error(e)



if __name__ == '__main__':
    args = sys.argv
    # crawler_util.headless = False
    # args = ['','questions.txt',os.getcwd(),'deepseek']

    log_dir = os.path.join(os.getcwd(), 'log')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, args[3] + '.log')
    logging = logging_config.setup_logger(log_file, 'geomonitor')
    handle(args[1], args[2], args[3])