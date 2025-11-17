# -*- coding=UTF-8 -*-
from flask import Flask, request
import json
import traceback
import deepseek
from playwright.sync_api import Playwright, sync_playwright, expect


app = Flask(__name__)



@app.route('/get_deepseek', methods=['GET', 'POST'])
def get_zaker_content():
    dict_s = request.json
    question = dict_s['question'].encode('utf-8').decode()
    print(question)
    result = {}
    result["status"] = '0'

    with sync_playwright() as playwright:
       
        result = main_headless.run_once(playwright, question)
        print(result)
    return json.dumps(result)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8016)

    # video_headless.get_readers("http://www.toutiao.com/video/7507415883602460735/")

