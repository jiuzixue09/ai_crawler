import asyncio
import json
import uuid
from datetime import datetime

import requests
import configparser

from CosService import CosService
from util import logging_config


class SpiderTask:

    def __init__(self, env):
        self.logging = logging_config.setup_logger('log/spider.log', self.__class__.__name__)
        # self.tasks = asyncio.Queue(maxsize=20)
        cos_config = configparser.ConfigParser()
        cos_config.read(f'config/{env}/config-oss.ini')
        self.o = CosService(cos_config)
        self.bucket_name = cos_config.get('connection','bucket_name')
        self.bucket_url = cos_config.get('connection','bucket_url')


    async def task_producer(self, query_api: str, model_id: int, tasks: asyncio.Queue) -> None:
        while True:
            now = datetime.now().strftime('%Y-%m-%d')
            res = requests.get(query_api.format(date=now,model_type=model_id))
            json_data = res.json()
            self.logging.info(json_data)
            task_list = json_data['data']['taskList']

            if not task_list:
                await asyncio.sleep(60 * 60)
            else:
                for task in task_list:
                    t = {'question': task['question'],
                         'task_id': task['taskDetailId']}
                    self.logging.info(t)
                    await tasks.put(t)

    async def task_consumer(self, update_api: str, spider, q: asyncio.Queue) -> None:
        while True:
            try:
                task = await q.get()
                question = task['question']
                task_id = task['task_id']

                try:
                    json_data = await spider.run_once(question)
                    json_data['taskid'] = task_id
                    if 'screenshot' in json_data:
                        key = "{}/{}.{}".format(spider.__class__.__name__.lower(), uuid.uuid1(), 'png')
                        self.o.upload_file_to_oss(json_data['screenshot'], self.bucket_name, key)
                        cos_url = self.bucket_url + key
                        json_data['cos_url'] = cos_url


                    self.logging.info(json_data)
                except Exception as e:
                    json_data = {'runStatus': 0, 'taskid': task_id}
                    self.logging.error(e)


                res = requests.post(update_api,json=json_data)
                self.logging.info(json.loads(res.content))
            except Exception as e:
                self.logging.error(e)

