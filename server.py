#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from waitress import serve #serveur de production
from flask import Flask #serveur web python
from swagger_ui import api_doc

import json
import random
import os

spec_string = '{"openapi":"3.0.1","info":{"title":"python-swagger-ui test api","description":"python-swagger-ui test api","version":"1.0.0"},"servers":[{"url":"http://127.0.0.1:8989/api"}],"tags":[{"name":"default","description":"default tag"}],"paths":{"/hello/world":{"get":{"tags":["default"],"summary":"output hello world.","responses":{"200":{"description":"OK","content":{"application/text":{"schema":{"type":"object","example":"Hello World!!!"}}}}}}}},"components":{}}'

app = Flask(__name__)

working_dir = os.path.dirname(os.path.abspath(__file__))
conf_path = os.path.join(working_dir, 'config/swagger.yml')

api_doc(app, config_path=conf_path, url_prefix='/api/doc', title='API DIM')

@app.route('/')
def hello_world():
    return "<h1> Hello World! </h1>"

@app.route('/test')
def display_random_list():
    list = []
    for i in range(0,5):
        list.append(random.randint(1,10))
    return json.dumps(list)     

serve(app, host='0.0.0.0', port=8080)