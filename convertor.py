"""Convert matter objects into yaml"""

from typing import List, Optional, Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape, Template
from matter_server.client.models.node import MatterNode, MatterEndpoint
from chip.clusters.ClusterObjects import Cluster
from chip.clusters.Objects import OnOff


env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape()
)


def _cluster_to_jinja_template(cluster: Cluster) -> Optional[Template]:
    template_name = _cluster_to_template_name(cluster)
    return None if template_name is None else env.get_template(template_name)


def _cluster_to_template_name(cluster: Cluster) -> Optional[str]:
    match cluster:
        case OnOff():
            return "paths/on_off.yml.j2"
        case _:
            return None


def _render_cluster(cluster: Cluster, **template_args) -> str:
    # return open(template, 'r', encoding="utf-8").read()
    return _cluster_to_jinja_template(cluster).render(**template_args)


def _endpoint_to_template_names(endpoint: MatterEndpoint) -> List[str]:
    """Tous les noms des templates de l'endpoint"""
    return [
        _cluster_to_template_name(cluster)
        for id, cluster in endpoint.clusters.items()
        if _cluster_to_template_name(cluster) is not None
    ]


def node_to_template_names(node: MatterNode) -> Dict[int, List[str]]:
    """Tous les noms de tous les templates par endpoint du node"""
    return {
        endpoint_id: _endpoint_to_template_names(endpoint)
        for endpoint_id, endpoint in node.endpoints.items()
    }
