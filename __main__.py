""" 
========================= Matter API python server =========================
The goal here is to make a ready for use python server in order to display 
Matter IOT devices API from a cluster/API converter.
This server works on Flask (3.0.2) | jinja (3.1.3) and waitress (3.0.0) for 
production server. 
It displays dynamically OpenApi 3.0 with swagger-ui-py (23.9.23)
=============================================================================
"""

from dynamic_render import register_new_renderer # render open api dynamic
import random
import json
import os

from waitress import serve  # production server
from flask import Flask, redirect, render_template, request  # web python server
from swagger_ui.core import ApplicationDocument # open api
from swagger_ui import api_doc
from jinja2 import Environment, FileSystemLoader, select_autoescape # config template


app = Flask(__name__)

environment = Environment(
    loader=FileSystemLoader(searchpath="./"),
    autoescape=select_autoescape()
)

working_dir = os.path.dirname(os.path.abspath(__file__))
conf_path = os.path.join(working_dir, 'config/swagger.yml')

api_doc(app, config_path=conf_path, url_prefix='/api/doc', title='API DIM')
api_renderer=register_new_renderer(app, "/swagger/blueprint")

@app.route('/')
def redirect_internal():
    return redirect("/html/devices", code=302)

@app.route('/html/devices')
def devices_menu():
    """ Road to display devices id from list and select them """
    server_ip=request.headers.get("Host").split(':')[0]
    html_template=environment.get_template("ressources/devices.html")
    
    return render_template(html_template, devices=[1,2,3], server_ip=f"{server_ip}", port="8080")
    

@app.route('/api/doc/')
@app.route('/api/doc/<id>')
def display_swagger(id):
    """ Road to display the swagger API of a devices """
    server_ip=request.headers.get("Host").split(':')[0]
    """ TODO methode to retrieve cluster_path for swagger.yml """
    cluster_paths = ["A", "B", "C"] 
    
    swagger_template=environment.get_template("config/swagger.yml")
    config_string=swagger_template.render(server_ip=f"{server_ip}", paths=cluster_paths)
    
    print(config_string)
    
    
    #api_doc=dynamic_render.ApplicationDocument(None, config_spec=config_string, url_prefix="/api/v0", title="API DIM")
    
    return api_renderer.from_string(config_spec=config_string)

@app.route('/test')
def display_random_list():
    """ TODO """
    list = []
    for i in range(0, 5):
        list.append(random.randint(1, 10))
    return json.dumps(list)


if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8080)
