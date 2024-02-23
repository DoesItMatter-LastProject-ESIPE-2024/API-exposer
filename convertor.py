"""Convert matter objects into yaml"""

from typing import Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape, Template
from matter_server.client.models.node import MatterNode, MatterEndpoint
from chip.clusters.ClusterObjects import Cluster
from chip.clusters.Objects import OnOff


env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape()
)


def _cluster_to_template_name(cluster: Cluster) -> Optional[str]:
    match cluster:
        case OnOff():
            return "paths/on_off.yml.j2"
        case _:
            return None


def _cluster_to_jinja_template(cluster: Cluster) -> Optional[Template]:
    template_name = _cluster_to_template_name(cluster)
    return None if template_name is None else env.get_template(template_name)


def _render_cluster(cluster: Cluster, node_id: int, endpoint_id: int) -> Optional[str]:
    """Renders a cluster into its OpenAPI yaml format"""
    jinja_template = _cluster_to_jinja_template(cluster)
    return None if jinja_template is None else jinja_template.render(node_id=node_id, endpoint_id=endpoint_id)


def _render_endpoint(endpoint: MatterEndpoint) -> Optional[str]:
    """Renders an endpoint into its OpenAPI yaml format"""
    rendered_cluster_list = [
        _render_cluster(cluster, node_id=endpoint.node.node_id,
                        endpoint_id=endpoint.endpoint_id)
        for cluster in endpoint.clusters.values()
    ]
    rendered_cluster_list = [
        rendered_cluster for rendered_cluster in rendered_cluster_list
        if rendered_cluster is not None
    ]
    return None if len(rendered_cluster_list) == 0 else "\n\n".join(rendered_cluster_list)


def render_node(node: MatterNode) -> Optional[str]:
    """Renders a node into its OpenAPI yaml format"""
    rendered_endpoint_list = [
        _render_endpoint(endpoint)
        for endpoint in node.endpoints.values()
    ]
    rendered_endpoint_list = [
        rendered_endpoint for rendered_endpoint in rendered_endpoint_list
        if rendered_endpoint is not None
    ]
    return None if len(rendered_endpoint_list) == 0 else "\n\n".join(rendered_endpoint_list)
