"""This is the entry point of the server."""

import logging
import tempfile
import shutil
from typing import AsyncGenerator, Callable, Coroutine, Dict, Any
from dataclasses import asdict
from asyncio import run, sleep

from httpx import AsyncClient
# web python server
from uvicorn import Server, Config
from fastapi.applications import FastAPI
from fastapi.requests import Request
from fastapi.exceptions import HTTPException
from fastapi.responses import Response, RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from playsound import playsound

# templating
from jinja2 import Environment, select_autoescape, FileSystemLoader

from chip.clusters.CHIPClusters import ChipClusters

from api_exposer.my_client import MyClient
from api_exposer.renderer import Renderer
from api_exposer.validator import (
    validate_node_id,
    validate_endpoint_id,
    validate_cluster_name,
    validate_event_name,
    validate_attribute_name,
    validate_command_name,
    validate_json_body,
    validate_json_attribute)
from api_exposer.argument_parser import parse_args
from api_exposer.const import SWAGGER_TEMPLATE_FOLDER, SWAGGER_HTML_FOLDER, STATIC_FOLDER

SWAGGER_PATH = 'html/swagger'
ATTRIBUTE_LIST_ID = 0x0000FFFB
ACCEPTED_COMMAND_LIST_ID = 0x0000FFF9
EVENT_LIST_ID = 0x0000FFFA


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

    cluster_infos = ChipClusters(None)
    convertor = Renderer(
        client,
        cluster_infos,
        ATTRIBUTE_LIST_ID,
        ACCEPTED_COMMAND_LIST_ID)

    event_subscribers: Dict[str, Callable[[], None]] = {}
    attribute_subscribers: Dict[str, Callable[[], None]] = {}

    @app.get('/')
    def redirect():
        """Redirect user to the good page"""
        return RedirectResponse(url='/html/nodes')

    @app.get('/html/nodes', response_class=HTMLResponse)
    def devices_menu(request: Request):
        """Returns a html menu composed of device's id from list"""
        return html_template.TemplateResponse(
            request=request,
            name='nodes.html',
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
    async def node_api_documentation(request: Request, node_id: int) -> str:
        """Returns an OpenAPI documentation in yaml format for a matter node"""
        node = validate_node_id(client, node_id)
        cluster_paths = await convertor.render_node(node)

        content = env.get_template('swagger.yml.j2').render({
            'server_ip': request.url.hostname,
            'server_port': request.url.port,
            'paths': cluster_paths
        })
        return Response(
            media_type='application/yaml',
            content=content,
            headers={
                'Cache-control': 'no-cache'
            }
        )

    @app.post('/echo')
    async def echo(request: Request) -> None:
        """Prints the json body in the console"""
        print(await validate_json_body(request))

    @app.post('/dingdong')
    def dingdong() -> None:
        """Plays a dingdong sound"""
        with tempfile.TemporaryDirectory() as directory:
            filename = shutil.copy2(
                './attention_tone_sm30-96953.mp3',
                directory)
            logging.info('Playing sound %s', filename)
            playsound(filename)

    def _event_path(
            node_id: int,
            endpoint_id: int,
            cluster_name: str,
            event_name: str,
            callback_name: str) -> str:
        return f'{node_id}/{endpoint_id}/{cluster_name}/{event_name}/{callback_name}'

    @app.post('/api/v1/{node_id}/{endpoint_id}/{cluster_name}/subscribe/event/{event_name}')
    async def subscribe_to_event(
            request: Request,
            node_id: int,
            endpoint_id: int,
            cluster_name: str,
            event_name: str):
        """Adds an URL to the subscription list of the event to be called with a POST request when an event is updated."""
        json_body = await validate_json_body(request)
        callback_name = validate_json_attribute(json_body, 'callback_name')
        callback_url = validate_json_attribute(json_body, 'callback_url')
        node = validate_node_id(client, node_id)
        endpoint = validate_endpoint_id(node, endpoint_id)
        cluster = validate_cluster_name(endpoint, cluster_name)
        event = validate_event_name(cluster, event_name)
        path = _event_path(
            node_id,
            endpoint_id,
            cluster_name,
            event_name,
            callback_name)

        async def callback(data):
            json_data = asdict(data)
            logging.debug('calling %s with %s', callback_url, json_data)
            async with AsyncClient() as client:
                await client.post(callback_url, json=json_data)

        if path in event_subscribers:
            raise HTTPException(400, f'callback {callback_name} already exist')
        event_subscribers[path] = client.subscribe_to_event(
            node_id, endpoint_id, cluster.id, event.event_id, callback)
        logging.debug('there is %d subscribers', len(event_subscribers))

    @app.delete('/api/v1/{node_id}/{endpoint_id}/{cluster_name}/subscribe/event/{event_name}/{callback_name}')
    def unsubscribe_to_event(
            node_id: int,
            endpoint_id: int,
            cluster_name: str,
            event_name: str,
            callback_name: str):
        """Removes a REST Endpoint to the subscription list of the event"""
        path = _event_path(
            node_id,
            endpoint_id,
            cluster_name,
            event_name,
            callback_name)
        if path not in event_subscribers:
            logging.info('callback at %s not found', path)
            raise HTTPException(404, f'callback {callback_name} not found')
        event_subscribers[path]()
        del event_subscribers[path]

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
        attribute_info = validate_attribute_name(
            cluster_infos, cluster, attribute_name)
        attribute = await client.read_cluster_attribute(
            node_id, endpoint_id, cluster.id, attribute_info.get('attributeId'))
        return JSONResponse(content={attribute_name: attribute})

    @app.patch('/api/v1/{node_id}/{endpoint_id}/{cluster_name}/attribute/{attribute_name}')
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
        attribute_info = validate_attribute_name(
            cluster_infos, cluster, attribute_name)

        json_body = await validate_json_body(request)
        attribute_value = validate_json_attribute(json_body, attribute_name)

        new_attribute = await client.write_cluster_attribute(
            node_id,
            endpoint_id,
            cluster.id,
            attribute_info.get('attributeId'),
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
        cluster = validate_cluster_name(
            endpoint, cluster_name)
        command_class = validate_command_name(
            cluster, command_name)

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
