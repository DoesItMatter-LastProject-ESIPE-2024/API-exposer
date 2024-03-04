"""This is the entry point of the server."""

from argparse import ArgumentParser

from asyncio import run
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

from nodes import Nodes
from convertor import render_node
from const import DEFAULT_SERVER_URL
from validator import validate_node_id, validate_endpoint_id, validate_cluster_name, validate_attribute_name, validate_command_name

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

    args = parser.parse_args()

    # configure logging
    handlers = [logging.FileHandler(args.log_file)] if args.log_file else None
    logging.basicConfig(handlers=handlers, level=args.log_level.upper())

    nodes_client = Nodes(args.url)
    await nodes_client.start()
    nodes = nodes_client.nodes

    app = FastAPI()
    app.mount('/static', StaticFiles(directory='static'), name='static')
    html_template = Jinja2Templates(directory='dynamic')

    env = Environment(
        loader=FileSystemLoader('config'),
        autoescape=select_autoescape()
    )

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
                'port': 8080,
                'swagger_path': SWAGGER_PATH
            }
        )

    @app.get(f'/{SWAGGER_PATH}/{{node_id}}')
    def swagger_ui(request: Request, node_id: int):
        """Dynamically renders a swagger ui with the correct documentation"""
        validate_node_id(nodes_client, node_id)
        return html_template.TemplateResponse(
            request=request,
            name='swagger.html',
            context={'node_id': node_id}
        )

    @app.get('/api/doc/{node_id}')
    def node_api_documentation(request: Request, node_id: int) -> str:
        """Returns an OpenAPI documentation in yaml format for a matter node"""
        node = validate_node_id(nodes_client, node_id)
        cluster_paths = render_node(node)

        content = env.get_template('swagger.yml.j2').render({
            'server_ip': request.url.hostname,
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
        node = validate_node_id(nodes_client, node_id)
        endpoint = validate_endpoint_id(node, endpoint_id)
        cluster = validate_cluster_name(endpoint, cluster_name)
        attribute_field = validate_attribute_name(cluster, attribute_name)
        attribute = await nodes_client.read_cluster_attribute(
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
        node = validate_node_id(nodes_client, node_id)
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

        new_attribute = await nodes_client.write_cluster_attribute(
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
        node = validate_node_id(nodes_client, node_id)
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
            return await nodes_client.send_cluster_command(node_id, endpoint_id, command)
        except Exception as err:
            logging.warning(
                'Unexpected error while handling a matter cluster command : %s', str(err))
            raise HTTPException(500, str(err)) from err

    config = Config(app, host='0.0.0.0', port=8080, log_level='info')
    server = Server(config)
    await server.serve()


if __name__ == '__main__':
    run(main())
