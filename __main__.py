""" 
========================= Matter API python server =========================
The goal here is to make a ready for use python server in order to display 
Matter IOT devices API from a cluster/API converter.
This server works on Flask (3.0.2) | jinja (3.1.3) and waitress (3.0.0) for 
production server. 
It displays dynamically OpenApi 3.0 with swagger-ui-py (23.9.23)
=============================================================================
"""

import asyncio
import random
import json
import os

from waitress import serve  # production server
from flask import Flask, redirect, render_template, render_template_string, request  # web python server
from jinja2 import Environment, FileSystemLoader, select_autoescape  # config template

from dynamic_render import register_new_renderer  # render open api dynamic
from convertor import render_node
from nodes import Nodes
from const import DEFAULT_SERVER_URL


async def main():
    """The main function of the server, """
    nodes_client = Nodes(DEFAULT_SERVER_URL)
    await nodes_client.start()
    nodes = nodes_client.nodes

    working_dir = os.path.dirname(os.path.abspath(__file__))
    static_folder_path = os.path.join(working_dir, 'static')

    name = __name__.split('.', maxsplit=1)[0]
    app = Flask(name, static_folder=static_folder_path)

    environment = Environment(
        loader=FileSystemLoader(searchpath="./"),
        autoescape=select_autoescape()
    )

    api_renderer = register_new_renderer(app, "/swagger/blueprint")

    SWAGGER_PATH = 'html/swagger'

    @app.route('/')
    def redirect_internal():
        """Redirects index to html/devices"""
        return redirect("/html/devices", code=302)

    @app.route('/html/devices')
    def devices_menu():
        """Returns a html menu composed of device's id from list"""
        server_ip = request.headers.get("Host").split(':')[0]
        html_template = environment.get_template("dynamic/devices.html")

        devices = list(nodes.keys())

        return render_template(
            html_template,
            devices=devices,
            server_ip=f"{server_ip}",
            port="8080",
            swagger_path=SWAGGER_PATH
        )

    @app.route(f'/{SWAGGER_PATH}/<int:node_id>')
    def swagger_ui(node_id: int):
        """Dynamically renders a swagger ui with the correct documentation"""
        doc = node_api_documentation(node_id)
        if doc == 404:
            return render_template_string("Error: 404 not found", code=404)
        return api_renderer.from_string(doc)

    @app.route('/api/doc/<int:node_id>')
    def node_api_documentation(node_id: int) -> str:
        """Returns an OpenAPI documentation in yaml format for a matter node"""
        server_ip = request.headers.get("Host").split(':')[0]

        node = nodes[node_id]
        if node is None:
            return 404
        cluster_paths = render_node(node)

        swagger_template = environment.get_template("config/swagger.yml")
        return swagger_template.render({
            "server_ip": server_ip,
            "paths": cluster_paths
        })

    @app.route('/test')
    def display_random_list():
        """Returns a json list of 5 random number between 1,10 in json format"""
        return json.dumps([random.randint(1, 10) for _ in range(0, 5)])

    serve(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    asyncio.run(main())
