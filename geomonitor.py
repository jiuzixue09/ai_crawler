import asyncio
import os
import random
import sys

from spider import deepseek, yuan_bao, chat_gpt, dou_bao, bai_du
from util import excel_util, crawler_util, logging_config


async def handle(file_path, output_path, selected):
    site_map = {'baidu': bai_du.BaiDu, 'deepseek': deepseek.DeepSeek, 'doubao': dou_bao.DouBao, 'yuanbao': yuan_bao.YuanBao,
                'chartgpt': chat_gpt.ChatGpt}


    if selected == 'all':
        site_crawlers = [bai_du.BaiDu, deepseek.DeepSeek, dou_bao.DouBao, yuan_bao.YuanBao] #, chat_gpt.ChatGpt
    else:
        site_crawlers = [site_map.get(selected)]

    questions = []
    with open(file_path, 'r') as file:
        for l in file:
            questions.append(l)

    background_tasks = set()
    for site_crawler in site_crawlers:
        op = os.path.join(output_path,site_crawler.__name__ + '.xlsx')
        task = asyncio.create_task(search(questions, op, site_crawler()))
        background_tasks.add(task)

    for t in background_tasks:
        await t



async def search(questions, output_path, site_crawler):
    eu = excel_util.ExcelUtil()
    for question in questions:
        try:
            data_json = await site_crawler.run_once(question)
            data = [question, data_json['article'], data_json['share_link'], str(data_json.get('list', ''))]
            logging.info(data_json)

            eu.append_excel(data)
            eu.save_excel(output_path)
            if site_crawler.__class__ == yuan_bao.YuanBao:

                await asyncio.sleep(random.randint(30, 60))
            elif site_crawler.__class__ in [deepseek.DeepSeek, dou_bao.DouBao]:
                await asyncio.sleep(random.randint(5, 10))

        except Exception as e:
            # raise e
            logging.error(e)



if __name__ == '__main__':
    args = sys.argv
    # crawler_util.headless = False
    # args = ['','questions.txt',os.getcwd(),'all']

    log_dir = os.path.join(os.getcwd(), 'log')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, args[3] + '.log')
    logging = logging_config.setup_logger(log_file, 'geomonitor')
    asyncio.run(handle(args[1], args[2], args[3]))
