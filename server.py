""" TODO description + renommer en __main__.py """

import json
import random
import os

from waitress import serve  # serveur de production
from flask import Flask  # serveur web python
from swagger_ui import api_doc


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
