""" 
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

from chip.clusters import Objects
from chip.clusters.Objects import OnOff
from chip.clusters.ClusterObjects import Cluster, ClusterCommand, ClusterObject, ClusterObjectFieldDescriptor
from matter_server.client.models.node import MatterNode, MatterEndpoint

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

    def _client_error(code: int, msg: str):
        logging.warning(msg)
        raise HTTPException(code, msg)

    def _bad_request(msg: str):
        _client_error(400, msg)

    def _not_found(msg: str):
        _client_error(404, msg)

    def _validate_node_id(node_id: int) -> MatterNode:
        if node_id not in nodes:
            _not_found(f'node {node_id} not found')
        return nodes[node_id]

    def _validate_endpoint_id(node: MatterNode, endpoint_id: int) -> MatterEndpoint:
        if endpoint_id not in node.endpoints:
            _not_found(f'endpoint {endpoint_id} not found')
        return node.endpoints[endpoint_id]

    def _validate_cluster_name(endpoint: MatterEndpoint, cluster_name: str) -> Cluster:
        if not hasattr(Objects, cluster_name):
            _not_found(f'cluster {cluster_name} not found')
        cluster_class = getattr(Objects, cluster_name)

        if not hasattr(cluster_class, 'id'):
            _not_found('cluster id not found')
        cluster_id = cluster_class.id

        if cluster_id not in endpoint.clusters:
            _not_found(f'cluster {cluster_id} not found in endpoint')
        return endpoint.clusters[cluster_id]

    def _validate_command_name(cluster: Cluster, command_name: str) -> type[ClusterCommand]:
        if not hasattr(cluster, 'Commands'):
            _not_found('cluster does not have commands')
        if not hasattr(cluster.Commands, command_name):
            _not_found(f'command {command_name} not found')
        return getattr(cluster.Commands, command_name)

    def _validate_attribute_name(cluster: Cluster, attribute_name: str) -> ClusterObjectFieldDescriptor:
        field = cluster.descriptor.GetFieldByLabel(attribute_name)
        if field is None:
            _not_found(f'cluster does not have {attribute_name}')
        return field

    # def _validate_attribute_name(cluster: Cluster, attribute_name: str) -> Any:
    #     if not hasattr(cluster, attribute_name):
    #         _not_found(f'cluster does not have {attribute_name}')
    #     return getattr(cluster, attribute_name)

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
        _validate_node_id(node_id)
        return html_template.TemplateResponse(
            request=request,
            name='swagger.html',
            context={'node_id': node_id}
        )

    @app.get('/api/doc/{node_id}')
    def node_api_documentation(request: Request, node_id: int) -> str:
        """Returns an OpenAPI documentation in yaml format for a matter node"""
        node = _validate_node_id(node_id)
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
            request: Request,
            node_id: int,
            endpoint_id: int,
            cluster_name: str,
            attribute_name: str):
        """Return attribute state in json format"""
        node = _validate_node_id(node_id)
        endpoint = _validate_endpoint_id(node, endpoint_id)
        cluster = _validate_cluster_name(endpoint, cluster_name)
        attribute_field = _validate_attribute_name(cluster, attribute_name)
        attribute = await nodes_client.read_cluster_attribute(
            node_id, endpoint_id, cluster.id, attribute_field.Tag)
        return JSONResponse(content={f'{attribute_name}': attribute})

    @app.post('/api/v1/{node_id}/{endpoint_id}/{cluster_name}/attribute/{attribute_name}')
    async def set_attribute(
            request: Request,
            node_id: int,
            endpoint_id: int,
            cluster_name: str,
            attribute_name: str):
        """Update attribute state"""
        node = _validate_node_id(node_id)
        endpoint = _validate_endpoint_id(node, endpoint_id)
        cluster = _validate_cluster_name(endpoint, cluster_name)
        attribute_field = _validate_attribute_name(cluster, attribute_name)

        new_state = (await request.json())[attribute_name]

        attribute = await nodes_client.write_cluster_attribute(
            node_id, endpoint_id, cluster.id, attribute_field.Tag, new_state)
        return JSONResponse(content={f'{attribute_name}': attribute})

    @app.post('/api/v1/{node_id}/{endpoint_id}/{cluster_name}/command/{command_name}')
    async def do_command(
            request: Request,
            node_id: int,
            endpoint_id: int,
            cluster_name: str,
            command_name: str):
        """Switch the state of the cluster on off"""
        node = _validate_node_id(node_id)
        endpoint = _validate_endpoint_id(node, endpoint_id)
        cluster = _validate_cluster_name(endpoint, cluster_name)
        command_class = _validate_command_name(cluster, command_name)

        if (await request.body()) == b'':
            command = command_class()
        else:
            command_parameters: Dict[str: Any] = await request.json()
            # if not type(command_parameters) == dict:
            #     # might not be true
            #     _bad_request('command parameters must be an object')
            command = command_class(**command_parameters)
        try:
            print(command)
            result = await nodes_client.send_cluster_command(node_id, endpoint_id, command)
            print(result)
        except Exception as err:
            _client_error(500, str(err))

    config = Config(app, host='0.0.0.0', port=8080, log_level='info')
    server = Server(config)
    await server.serve()


if __name__ == "__main__":
    run(main())
