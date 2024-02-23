"""This module is used to dynamically render an swagger ui page as html"""

from swagger_ui.core import ApplicationDocument
from flask import Flask
from flask import request
from flask import jsonify
from flask.blueprints import Blueprint


def register_new_renderer(app: Flask, url: str):
    """Instantiate a renderer and registers it to the flask app at the specified url."""
    renderer = Renderer(app, url)
    renderer._register_blueprint()
    return renderer


class Renderer:
    """Generates html swagger ui pages from configurations"""

    def __init__(self, app: Flask, url: str) -> None:
        self.current_doc: ApplicationDocument = None
        self.app = app
        self.url = url

    def from_string(self, config_spec: str):
        """Generates a swagger ui html page from a specification string."""
        self.current_doc = ApplicationDocument(
            self.app,
            config_spec=config_spec,
            url_prefix=self.url)
        return self.current_doc.doc_html

    def _register_blueprint(self):
        self.current_doc = ApplicationDocument(
            self.app,
            config_spec='{"openapi":"3.0.1","info":{"title":"python-swagger-ui test api","description":"python-swagger-ui test api","version":"1.0.0"}}',
            url_prefix=self.url)
        swagger_blueprint = Blueprint(
            'SWAGGER_BP',
            __name__,
            url_prefix=self.url,
            static_folder=self.current_doc.static_dir,
            static_url_path=self.current_doc.static_uri_relative,
        )

        @swagger_blueprint.route(self.current_doc.root_uri_relative(slashes=True))
        @swagger_blueprint.route(self.current_doc.root_uri_relative(slashes=False))
        def swagger_blueprint_doc_handler():
            return self.current_doc.doc_html

        @swagger_blueprint.route(self.current_doc.editor_uri_relative(slashes=True))
        @swagger_blueprint.route(self.current_doc.editor_uri_relative(slashes=False))
        def swagger_blueprint_editor_handler():
            return self.current_doc.editor_html

        @swagger_blueprint.route(self.current_doc.swagger_json_uri_relative)
        def swagger_blueprint_config_handler():
            return jsonify(self.current_doc.get_config(request.host))

        self.app.register_blueprint(swagger_blueprint)
