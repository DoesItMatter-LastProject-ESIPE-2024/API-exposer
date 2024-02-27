"""Convert matter objects into yaml"""

import inspect
from inspect import isclass, getmembers
from typing import Optional, List
from jinja2 import Environment, FileSystemLoader, select_autoescape
from matter_server.client.models.node import MatterNode, MatterEndpoint
from chip.clusters.ClusterObjects import Cluster, ClusterObjectFieldDescriptor, ClusterCommand
from chip.clusters.Objects import OnOff


env = Environment(
    loader=FileSystemLoader("templates/paths"),
    autoescape=select_autoescape()
)


def _render_attribute(node_id: int, endpoint_id: int, cluster: Cluster, attribute: ClusterObjectFieldDescriptor) -> Optional[str]:
    """Renders an attribute into its OpenAPI yaml format"""
    jinja_template = env.get_template("attributes.yml.j2")
    return None if jinja_template is None else jinja_template.render(
        node_id=node_id,
        endpoint_id=endpoint_id,
        cluster_name=cluster.__class__.__name__,
        attribute_name=attribute.Label,
        attribute_type=attribute.Type
    )


def _render_command(node_id: int, endpoint_id: int, cluster: Cluster, command: type[ClusterCommand]) -> Optional[str]:
    """Renders a command into its OpenAPI yaml format"""
    jinja_template = env.get_template("commands.yml.j2")
    return None if jinja_template is None else jinja_template.render(
        node_id=node_id,
        endpoint_id=endpoint_id,
        cluster_name=cluster.__class__.__name__,
        command_name=command.__name__
    )


def _render_path_by_attributes(node_id: int, endpoint_id: int, cluster: Cluster) -> List[str]:
    """Renders the attributes of a cluster into its OpenAPI yaml format"""
    rendered_attribute_list = [
        _render_attribute(node_id, endpoint_id, cluster, attribute)
        for attribute in cluster.descriptor.Fields
    ]
    rendered_attribute_list = [
        rendered_attribute for rendered_attribute in rendered_attribute_list
        if rendered_attribute is not None
    ]
    return rendered_attribute_list


def _render_path_by_commands(node_id: int, endpoint_id: int, cluster: Cluster) -> List[str]:
    """Renders the commands of a cluster into its OpenAPI yaml format"""
    rendered_command_list = [
        _render_command(node_id, endpoint_id, cluster, command)
        for command in _get_all_commands(cluster)
    ]
    rendered_command_list = [
        rendered_attribute for rendered_attribute in rendered_command_list
        if rendered_attribute is not None
    ]
    return rendered_command_list


def _render_path_by_cluster(node_id: int, endpoint_id: int, cluster: Cluster) -> List[str]:
    """Renders a cluster into its OpenAPI yaml format"""
    rendered_attribute_list = _render_path_by_attributes(node_id, endpoint_id, cluster)
    rendered_command_list = _render_path_by_commands(node_id, endpoint_id, cluster)
    rendered_cluster_list = rendered_attribute_list + rendered_command_list
    return rendered_cluster_list


def _render_path_by_endpoint(endpoint: MatterEndpoint) -> List[str]:
    """Renders an endpoint into its OpenAPI yaml format"""
    rendered_cluster_list = [
        _render_path_by_cluster(node_id=endpoint.node.node_id,
                        endpoint_id=endpoint.endpoint_id, cluster=cluster)
        for cluster in endpoint.clusters.values()
    ]
    rendered_cluster_list = _flat_map(rendered_cluster_list)
    rendered_cluster_list = [
        rendered_cluster for rendered_cluster in rendered_cluster_list
        if rendered_cluster is not None
    ]
    return rendered_cluster_list


def render_node(node: MatterNode) -> Optional[str]:
    """Renders a node into its OpenAPI yaml format"""
    rendered_endpoint_list = [
        _render_path_by_endpoint(endpoint)
        for endpoint in node.endpoints.values()
    ]
    rendered_endpoint_list = _flat_map(rendered_endpoint_list)
    rendered_endpoint_list = [
        rendered_endpoint for rendered_endpoint in rendered_endpoint_list
        if rendered_endpoint is not None
    ]
    return None if len(rendered_endpoint_list) == 0 else "\n\n".join(rendered_endpoint_list)


def _flat_map(list2d: List[List[str]]) -> List[str]:
    return [
        item
        for items in list2d
        for item in items
    ]

def _get_all_commands(cluster: Cluster):
    if not hasattr(cluster.__class__, 'Commands'):
        return []
    return [cmd_class for _, cmd_class in getmembers(
        cluster.__class__.Commands,
        lambda member: isclass(member) and issubclass(member, ClusterCommand)
    )]
