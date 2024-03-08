"""This is the entry point of the server."""

from asyncio import run
import json
import logging
from typing import Dict, Any

# web python server
from uvicorn import Server, Config
from fastapi.applications import FastAPI
from fastapi.requests import Request
from fastapi.exceptions import HTTPException
from fastapi.responses import Response, RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# templating
from jinja2 import Environment, select_autoescape, FileSystemLoader

from api_exposer.my_client import MyClient
from api_exposer.convertor import Convertor
from api_exposer.validator import validate_node_id, validate_endpoint_id, validate_cluster_name, validate_attribute_name, validate_command_name
from api_exposer.argument_parser import parse_args
from api_exposer.const import SWAGGER_TEMPLATE_FOLDER, SWAGGER_HTML_FOLDER, STATIC_FOLDER, FEATURES_JSON_FOLDER
from api_exposer.feature import Features

SWAGGER_PATH = 'html/swagger'


async def main():
    """The main function of the server"""
    args = parse_args()

    client = MyClient(args.url)
    await client.start()
    nodes = client.nodes

    app = FastAPI()
    app.mount('/static', StaticFiles(directory=STATIC_FOLDER), name='static')
    html_template = Jinja2Templates(directory=SWAGGER_HTML_FOLDER)

    env = Environment(
        loader=FileSystemLoader(SWAGGER_TEMPLATE_FOLDER),
        autoescape=select_autoescape()
    )

    with open(FEATURES_JSON_FOLDER, 'r', encoding='utf-8') as f:
        clusters: Dict[str, Any] = json.load(f)

    features = {
        int(id): Features.__from_json__(json_feature)
        for id, json_feature in clusters.items()
    }
    convertor = Convertor(features)

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
                'server_ip': request.url.hostname,
                'server_port': request.url.port,
                'swagger_path': SWAGGER_PATH
            }
        )

    @app.get(f'/{SWAGGER_PATH}/{{node_id}}')
    def swagger_ui(request: Request, node_id: int):
        """Dynamically renders a swagger ui with the correct documentation"""
        validate_node_id(client, node_id)
        return html_template.TemplateResponse(
            request=request,
            name='swagger.html',
            context={'node_id': node_id}
        )

    @app.get('/api/doc/{node_id}')
    def node_api_documentation(request: Request, node_id: int) -> str:
        """Returns an OpenAPI documentation in yaml format for a matter node"""
        node = validate_node_id(client, node_id)
        cluster_paths = convertor.render_node(node)

        content = env.get_template('swagger.yml.j2').render({
            'server_ip': request.url.hostname,
            'server_port': request.url.port,
            'paths': cluster_paths
        })
        return Response(
            media_type='application/x-yaml',
            content=content,
            headers={
                'Cache-control': 'no-cache'
            }
        )

    @app.get('/api/v1/{node_id}/{endpoint_id}/{cluster_name}/attribute/{attribute_name}')
    async def get_attribute(
            node_id: int,
            endpoint_id: int,
            cluster_name: str,
            attribute_name: str):
        """Returns an attribute of a node's endpoint in json format"""
        node = validate_node_id(client, node_id)
        endpoint = validate_endpoint_id(node, endpoint_id)
        cluster = validate_cluster_name(endpoint, cluster_name)
        attribute_field = validate_attribute_name(cluster, attribute_name)
        attribute = await client.read_cluster_attribute(
            node_id, endpoint_id, cluster.id, attribute_field.Tag)
        return JSONResponse(content={attribute_name: attribute})

    @app.post('/api/v1/{node_id}/{endpoint_id}/{cluster_name}/attribute/{attribute_name}')
    async def set_attribute(
            request: Request,
            node_id: int,
            endpoint_id: int,
            cluster_name: str,
            attribute_name: str):
        """Updates an attribute of a node's endpoint"""
        node = validate_node_id(client, node_id)
        endpoint = validate_endpoint_id(node, endpoint_id)
        cluster = validate_cluster_name(endpoint, cluster_name)
        attribute_field = validate_attribute_name(cluster, attribute_name)

        if (await request.body()) == b'':
            raise HTTPException(400, "missing POST body")
        json: Dict[str, any] = await request.json()
        if not isinstance(json, dict):
            raise HTTPException(400, "malformed json")

        attribute_value = json.get(attribute_name, None)
        if attribute_value is None:
            raise HTTPException(400, "missing attribute value")

        new_attribute = await client.write_cluster_attribute(
            node_id,
            endpoint_id,
            cluster.id,
            attribute_field.Tag,
            attribute_value)
        return JSONResponse(content={attribute_name: new_attribute})

    @app.post('/api/v1/{node_id}/{endpoint_id}/{cluster_name}/command/{command_name}')
    async def do_command(
            request: Request,
            node_id: int,
            endpoint_id: int,
            cluster_name: str,
            command_name: str):
        """Sends a matter cluster command to the matter server
        to execute on the correct node/endpoint."""
        node = validate_node_id(client, node_id)
        endpoint = validate_endpoint_id(node, endpoint_id)
        cluster = validate_cluster_name(endpoint, cluster_name)
        command_class = validate_command_name(cluster, command_name)

        if (await request.body()) == b'':
            command = command_class()
        else:
            command_parameters: Dict[str: Any] = await request.json()
            # if not type(command_parameters) == dict:
            #     # might not be true
            #     _bad_request('command parameters must be an object')
            command = command_class(**command_parameters)
        try:
            return await client.send_cluster_command(node_id, endpoint_id, command)
        except Exception as err:
            logging.warning(
                'Unexpected error while handling a matter cluster command : %s', str(err))
            raise HTTPException(500, str(err)) from err

    config = Config(app, host='0.0.0.0', port=args.port, log_level='info')
    server = Server(config)
    await server.serve()


if __name__ == '__main__':
    run(main())
