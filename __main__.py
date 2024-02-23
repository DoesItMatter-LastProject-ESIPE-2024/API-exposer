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

import asyncio
import uvicorn

from fastapi import FastAPI, Request

from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from nodes import Nodes
from convertor import render_node
from const import DEFAULT_SERVER_URL

SWAGGER_PATH = 'html/swagger'


async def main():
    """The main function of the server"""

    nodes_client = Nodes(DEFAULT_SERVER_URL)
    await nodes_client.start()
    nodes = nodes_client.nodes

    app = FastAPI()
    # app.mount("/static", StaticFiles(directory="static"), name="static")
    html_template = Jinja2Templates(directory="dynamic")
    swagger_template = Jinja2Templates(directory="config")

    @app.get('/')
    def redirect():
        """Redirect user to the good page"""
        return RedirectResponse(url="/html/nodes")

    @app.get('/html/nodes', response_class=HTMLResponse)
    def devices_menu(request: Request):
        """Returns a html menu composed of device's id from list"""
        devices = list(nodes.keys())

        return html_template.TemplateResponse(
            request=request,
            name="devices.html",
            context={
                "nodes": devices,
                "server_ip": request.client.host,
                "port": 8080,
                "swagger_path": SWAGGER_PATH
            }
        )

    @app.get(f'/{SWAGGER_PATH}/{{node_id}}')
    def swagger_ui(request: Request, node_id: int):
        """Dynamically renders a swagger ui with the correct documentation"""
        doc = node_api_documentation(request, node_id)
        if doc == 404:
            return JSONResponse({"404": "error 404 not found"})
        return doc

    @app.get('/api/doc/{node_id}')
    def node_api_documentation(request: Request, node_id: int) -> str:
        """Returns an OpenAPI documentation in yaml format for a matter node"""
        node = nodes[node_id]
        if node is None:
            print("not found")
            return 404
        cluster_paths = render_node(node)

        return swagger_template.TemplateResponse(
            request=request,
            name="swagger.yml",
            context={
                "server_ip": request.client.host,
                "paths": cluster_paths
            }
        )

    config = uvicorn.Config(app, host="0.0.0.0", port=8080, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
