import json
import logging
import random
import sys
import time

import requests

from util import crawler_util, logging_config
from CosService import CosService
from RabbitReceiveMq import RabbitReceiveMq
from spider import deepseek, yuan_bao, chat_gpt, dou_bao, bai_du
import configparser


class Main:


    def __init__(self):
        self.logging = logging_config.setup_logger('log/crawler.log', self.__class__.__name__)
        site_map = {'baidu': bai_du.BaiDu, 'deepseek': deepseek.DeepSeek, 'doubao': dou_bao.DouBao,
                    'yuanbao': yuan_bao.YuanBao,
                    'chatgpt': chat_gpt.ChatGpt}

        self.acked = False

        rabbit_config = configparser.ConfigParser()
        rabbit_config.read(f'config/{env}/config-rabbitmq.ini')

        api_config = configparser.ConfigParser()
        api_config.read(f'config/{env}/config-api.ini')
        self.update_api = api_config.get('api','update_api')

        oss_config = configparser.ConfigParser()
        oss_config.read(f'config/{env}/config-oss.ini')

        self.c = CosService(oss_config, connection_section='connection-model-tx')
        self.bucket_name_tx = oss_config.get('img-diffusers-lora-tx', 'bucket_name')
        self.bucket_url_tx = oss_config.get('img-diffusers-lora-tx', 'bucket_url')

        self.site_map = site_map

        self.r = RabbitReceiveMq(rabbit_config, 'img-diffusers-train-lora-all', heartbeat=2000)
        self.crawler = site_map.get('baidu')()


    def run(self):
        try:
            self.r.run(self.callback)
        except (Exception,):
            self.logging.exception('run error')

    def callback(self, ch, method, properties, body):
        message = {"status": 500}
        decode = body.decode('utf-8')
        logging.info(decode)
        js = json.loads(decode)
        try:
            data_json = self.crawler.run_once(js)
            data_json['local_ip'] = crawler_util.local_ip()
            requests.post(self.update_api, data=data_json, headers={'Content-Type': 'application/json'})

        except Exception as e:
            self.logging.exception('run error:', e)

        if self.crawler.__class__ == yuan_bao.YuanBao:
            time.sleep(random.randint(30, 60))
        elif self.crawler.__class__ in [deepseek.DeepSeek, dou_bao.DouBao]:
            time.sleep(random.randint(5, 10))


    def upload_to_tx(self, rs: dict, file_name, key):
        s = time.time()
        self.c.upload_file_to_oss(file_name, self.bucket_name_tx, key, retry=1)
        oss_url_tx = self.bucket_url_tx + key
        rs['model_tx_oss_url'] = oss_url_tx
        spend = time.time() - s
        self.logging.info('tx_oss_url=%s,time=%s', oss_url_tx, spend)

if __name__ == '__main__':
    args = sys.argv
    env = 'dev' if len(args) < 2 else args[1]

    while True:
        Main().run()
