""" 
========================= Matter API python server =========================
The goal here is to make a ready for use python server in order to display 
Matter IOT devices API from a cluster/API converter.
This server works on Flask (3.0.2) | jinja (3.1.3) and waitress (3.0.0) for 
production server. 
It displays dynamically OpenApi 3.0 with swagger-ui-py (23.9.23)
=============================================================================
"""

import random
import json
import os

from waitress import serve  # production server
from flask import Flask  # web python server
from swagger_ui import api_doc # open api


app = Flask(__name__)

working_dir = os.path.dirname(os.path.abspath(__file__))
conf_path = os.path.join(working_dir, 'config/swagger.yml')

api_doc(app, config_path=conf_path, url_prefix='/api/doc', title='API DIM')


@app.route('/')
def hello_world():
    """ TODO """
    return "<h1> Hello World! </h1>"


@app.route('/test')
def display_random_list():
    """ TODO """
    list = []
    for i in range(0, 5):
        list.append(random.randint(1, 10))
    return json.dumps(list)


if __name__ == "__main__":
    serve(app, host='0.0.0.0', port=8080)
