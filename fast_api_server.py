"""POC de fast API"""
import uvicorn

from fastapi import FastAPI, Request

from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

def main():
    app = FastAPI()
    #app.mount("/static", StaticFiles(directory="static"), name="static")
    html_template = Jinja2Templates(directory="dynamic")
    swagger_template = Jinja2Templates(directory="config")
    SWAGGER_PATH = 'html/swagger'

    @app.get("/")
    async def redirect():
        """Redirect user to the good page"""
        return RedirectResponse(url="/html/nodes")

    @app.get("/html/nodes", response_class=HTMLResponse)
    async def devices_menu(request: Request):
        """TODO"""
        return html_template.TemplateResponse(
            request=request,
            name="devices.html",
            context={
                "nodes":[1,2,3], 
                "server_ip":request.client.host,
                "port":8080,
                "swagger_path":SWAGGER_PATH
            }
        )

    @app.get(f'/{SWAGGER_PATH}/{{node_id}}')
    async def swagger_ui(request: Request, node_id: int):
        """Dynamically renders a swagger ui with the correct documentation"""
        return swagger_template.TemplateResponse(
            request=request,
            name="swagger.yml",
            context={
                "server_ip":request.client.host,
                "path":""
            }
        )

    @app.get("/test")
    async def test(request: Request):
        """Dynamically renders a swagger ui with the correct documentation"""
        return swagger_template.TemplateResponse(
            request=request,
            name="swagger.yml",
            context={
                "server_ip":request.client.host,
                "path":""
            }
        )

    uvicorn.run(app, host="0.0.0.0", port=8080)

if __name__ == "__main__":
    main()