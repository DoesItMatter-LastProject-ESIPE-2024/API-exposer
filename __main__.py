""" 
TODO
========================= Matter API python server =========================
The goal here is to make a ready for use python server in order to display 
Matter IOT devices API from a cluster/API converter.
This server works on Flask (3.0.2) | jinja (3.1.3) and waitress (3.0.0) for 
production server. 
It displays dynamically OpenApi 3.0 with swagger-ui-py (23.9.23)
=============================================================================
"""

from argparse import ArgumentParser

from asyncio import run
import logging
from typing import Optional
from uvicorn import Server, Config
from fastapi.applications import FastAPI
from fastapi.requests import Request
from fastapi.exceptions import HTTPException
from fastapi.responses import Response, RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from jinja2 import Environment, select_autoescape, FileSystemLoader

from nodes import Nodes
from convertor import render_node
from const import DEFAULT_SERVER_URL

SWAGGER_PATH = 'html/swagger'


async def main():
    """The main function of the server"""
    parser = ArgumentParser()

    parser.add_argument(
        '--server-url',
        type=str,
        dest='url',
        default=DEFAULT_SERVER_URL,
        help=f'Vendor ID for the Fabric, defaults to {DEFAULT_SERVER_URL}',
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='info',
        # pylint: disable=line-too-long
        help='Provide logging level. Example --log-level debug, default=info, possible=(critical, error, warning, info, debug)',
    )
    parser.add_argument(
        '--log-file',
        type=str,
        default=None,
        help='Log file to write to (optional).',
    )

    nodes_client = Nodes(DEFAULT_SERVER_URL)
    await nodes_client.start()
    nodes = nodes_client.nodes

    app = FastAPI()
    app.mount('/static', StaticFiles(directory='static'), name='static')
    html_template = Jinja2Templates(directory='dynamic')

    env = Environment(
        loader=FileSystemLoader('config'),
        autoescape=select_autoescape()
    )

    def _validate_node_id(node_id: int) -> None:
        if node_id not in nodes:
            msg = f'node {node_id} not found'
            logging.info(msg)
            raise HTTPException(404, msg)

    @app.get('/')
    def redirect():
        """Redirect user to the good page"""
        return RedirectResponse(url='/html/nodes')

    @app.get('/html/nodes', response_class=HTMLResponse)
    def devices_menu(request: Request):
        """Returns a html menu composed of device's id from list"""
        return html_template.TemplateResponse(
            request=request,
            name='devices.html',
            context={
                'nodes': list(nodes.keys()),
                'server_ip': request.client.host,
                'port': 8080,
                'swagger_path': SWAGGER_PATH
            }
        )

    @app.get(f'/{SWAGGER_PATH}/{{node_id}}')
    def swagger_ui(request: Request, node_id: int):
        """Dynamically renders a swagger ui with the correct documentation"""
        _validate_node_id(node_id)
        return html_template.TemplateResponse(
            request=request,
            name='swagger.html',
            context={'node_id': node_id}
        )

    @app.get('/api/doc/{node_id}')
    def node_api_documentation(request: Request, node_id: int) -> str:
        """Returns an OpenAPI documentation in yaml format for a matter node"""
        _validate_node_id(node_id)
        node = nodes[node_id]
        cluster_paths = render_node(node)

        content = env.get_template('swagger.yml.j2').render({
            'server_ip': request.client.host,
            'paths': cluster_paths
        })
        return Response(
            media_type='application/x-yaml',
            content=content,
            headers={
                'Cache-control': 'no-cache'
            }
        )

    config = Config(app, host='0.0.0.0', port=8080, log_level='info')
    server = Server(config)
    await server.serve()

if __name__ == '__main__':
    run(main())
