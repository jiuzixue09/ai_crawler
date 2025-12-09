import asyncio
from datetime import datetime

import requests

from util import logging_config


class SpiderTask:

    def __init__(self):
        self.logging = logging_config.setup_logger('log/spider.log', self.__class__.__name__)
        # self.tasks = asyncio.Queue(maxsize=20)

    async def task_producer(self, query_api: str, model_id: int, tasks: asyncio.Queue) -> None:
        while True:
            now = datetime.now().strftime('%Y-%m-%d')
            res = requests.get(query_api.format(date=now))
            json_data = res.json()
            self.logging.info(json_data)
            task_list = json_data['data']['taskList']

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
                    data_json = await spider.run_once(question)
                    data_json['taskid'] = task_id
                    self.logging.info(data_json)
                except Exception as e:
                    data_json = {'runStatus': 0, 'taskid': task_id}
                    self.logging.error(e)

                res = requests.post(update_api,json=data_json)
                print(res.content)
                self.logging.info(res.content)
            except Exception as e:
                self.logging.error(e)

