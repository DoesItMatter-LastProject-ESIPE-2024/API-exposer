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
from flask import Flask, redirect, render_template, request  # web python server
from jinja2 import Environment, FileSystemLoader, select_autoescape  # config template

from dynamic_render import register_new_renderer  # render open api dynamic

working_dir = os.path.dirname(os.path.abspath(__file__))
conf_path = os.path.join(working_dir, 'config/swagger.yml')
static_folder_path = os.path.join(working_dir, 'static')

name = __name__.split('.', maxsplit=1)[0]
app = Flask(name, static_folder=static_folder_path)

environment = Environment(
    loader=FileSystemLoader(searchpath="./"),
    autoescape=select_autoescape()
)

api_renderer = register_new_renderer(app, "/swagger/blueprint")
print(app.static_url_path)


@app.route('/')
def redirect_internal():
    return redirect("/html/devices", code=302)


@app.route('/html/devices')
def devices_menu():
    """ Road to display devices id from list and select them """
    server_ip = request.headers.get("Host").split(':')[0]
    html_template = environment.get_template("ressources/devices.html")

    return render_template(html_template, devices=[1, 2, 3], server_ip=f"{server_ip}", port="8080")


@app.route('/api/doc/')
@app.route('/api/doc/<id>')
def display_swagger(id):
    """ Road to display the swagger API of a devices """
    server_ip = request.headers.get("Host").split(':')[0]
    # """ TODO methode to retrieve cluster_path for swagger.yml """
    cluster_paths = ["A", "B", "C"]

    swagger_template = environment.get_template("config/swagger.yml")
    config_string = swagger_template.render(
        server_ip=f"{server_ip}", paths=cluster_paths)

    print(config_string)

    # api_doc=dynamic_render.ApplicationDocument(None, config_spec=config_string, url_prefix="/api/v0", title="API DIM")

    return api_renderer.from_string(config_spec=config_string)


@app.route('/test')
def display_random_list():
    """Returns a list of 5 random number between 1,10 in json format"""
    return json.dumps([random.randint(1, 10) for _ in range(0, 5)])


if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8080)
