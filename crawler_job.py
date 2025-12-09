import asyncio
import sys
from datetime import datetime

import requests


from spider_task import SpiderTask
from util import logging_config, crawler_util
from CosService import CosService
from spider import deepseek, yuan_bao, dou_bao, bai_du, chat_gpt
import configparser


class CrawlerJob:


    def __init__(self):
        self.logging = logging_config.setup_logger('log/crawler-job.log', self.__class__.__name__)

        #4: chat_gpt.ChatGpt,
        # site_map = {1: dou_bao.DouBao, 2: yuan_bao.YuanBao, 3: deepseek.DeepSeek, 5: bai_du.BaiDu}
        site_map = {5: bai_du.BaiDu}

        cos_config = configparser.ConfigParser()
        cos_config.read(f'config/{env}/config-oss.ini')
        self.o = CosService(cos_config)

        api_config = configparser.ConfigParser()
        api_config.read(f'config/{env}/config.ini')
        self.query_api = api_config.get('api', 'query_api')
        self.update_api = api_config.get('api', 'update_api')

        crawler_util.headless = api_config.getboolean('playwright', 'headless')
        self.site_map = site_map


    async def main(self):
        tasks = []
        for site_id,site_class in self.site_map.items():
            q = asyncio.Queue(maxsize=20)
            spider_task = SpiderTask()
            t1 = asyncio.create_task(spider_task.task_producer(self.query_api,site_id, q))

            t2 = asyncio.create_task(spider_task.task_consumer(self.update_api,site_class(), q))
            tasks.append(t1)
            tasks.append(t2)

        for task in tasks:
            await task


if __name__ == "__main__":
    args = sys.argv


    env = 'dev' if len(args) < 2 else args[1]
    cj = CrawlerJob()
    asyncio.run(cj.main())