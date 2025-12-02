import configparser
import time

import pika
from pika.exceptions import ConnectionBlockedTimeout, StreamLostError


class RabbitReceiveMq:
    def __init__(self, config: configparser.ConfigParser, channel_section, connection_section='connection',
                 arguments=None, **con_args):
        self.user_pwd = pika.PlainCredentials(config.get(connection_section, "user_name"),
                                              config.get(connection_section, "password"))
        self.arguments = arguments
        self.q_name = config.get(channel_section, "q_name")
        self.exchange = config.get(channel_section, "exchange")
        self.r_key = config.get(channel_section, "r_key")
        self.con_args = con_args
        self.config = config
        self.connection_section = connection_section
        self.channel = self.get_channel()

    def get_channel(self):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.config.get(self.connection_section, "host"),
                port=self.config.getint(self.connection_section, "port"),
                virtual_host=self.config.get(self.connection_section, "virtual_host"),
                credentials=self.user_pwd,
                **self.con_args
            )
        )
        channel = connection.channel()

        # 声明exchange，由exchange指定消息在哪个队列传递，如不存在，则创建.durable = True 代表exchange持久化存储，False 非持久化存储
        channel.exchange_declare(exchange=self.exchange, durable=True)

        if ',' in self.q_name:
            q_split = self.q_name.split(',')
            r_split = self.r_key.split(',')
            for q, r in zip(q_split, r_split):
                # 申明消息队列，消息在这个队列传递，如果不存在，则创建队列
                channel.queue_declare(queue=q, durable=True, arguments=self.arguments)
                channel.queue_bind(exchange=self.exchange,
                                   queue=q, routing_key=r)
        else:
            channel.queue_declare(queue=self.q_name, durable=True, arguments=self.arguments)
            channel.queue_bind(exchange=self.exchange,
                               queue=self.q_name, routing_key=self.r_key)

        channel.basic_qos(prefetch_count=1)

        return channel

    def close(self):
        try:
            self.channel.close()
        except:
            pass

    def run(self, message_callback):
        while True:
            try:
                if ',' in self.q_name:
                    for q in self.q_name.split(','):
                        self.channel.basic_consume(on_message_callback=message_callback, queue=q)
                else:
                    self.channel.basic_consume(on_message_callback=message_callback, queue=self.q_name)

                print("start consuming.")
                self.channel.start_consuming()
            except (ConnectionResetError, ConnectionBlockedTimeout, StreamLostError):
                self.close()
                print('rabbit receive mq reconnect')
                self.channel = self.get_channel()
                time.sleep(60)

