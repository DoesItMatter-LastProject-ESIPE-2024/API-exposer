"""Convert matter objects into yaml"""

from dataclasses import dataclass
import json
import logging
from inspect import isclass, getmembers
from typing import Dict, Optional, List, _GenericAlias, Set, TypeVar
from jinja2 import Environment, FileSystemLoader, select_autoescape
from matter_server.client.models.node import MatterNode, MatterEndpoint
from chip.clusters.ClusterObjects import Cluster, ClusterObjectFieldDescriptor, ClusterCommand

from api_exposer.const import SWAGGER_PATHS_TEMPLATE_FOLDER
from api_exposer.feature import FeatureComponents, Features


env = Environment(
    loader=FileSystemLoader(SWAGGER_PATHS_TEMPLATE_FOLDER),
    autoescape=select_autoescape()
)

T = TypeVar('T')


@dataclass
class Convertor:
    """TODO"""
    feature: Dict[int, Features]

    def _convert_type(self, class_type: type) -> str:
        match class_type:
            case _GenericAlias() | list() | set() | dict():
                # FIXME
                return 'null'
            case integer if issubclass(integer, int): return 'integer'
            case string if issubclass(string, str): return 'string'
            case _: return 'null'

    def _render_attribute(
            self,
            node_id: int,
            endpoint_id: int,
            endpoint_name: str,
            cluster: Cluster,
            attribute: ClusterObjectFieldDescriptor,
            feature: FeatureComponents) -> Optional[str]:
        """Renders an attribute path into its OpenAPI yaml format"""
        jinja_template = env.get_template("attributes.yml.j2")
        if jinja_template is None:
            return None

        match (feature.is_readable(attribute.Tag), feature.is_writable(attribute.Tag)):
            case (False, False):  # Neither get or post
                return None
            case (is_readable, is_writable):
                return jinja_template.render(
                    node_id=node_id,
                    endpoint_id=endpoint_id,
                    endpoint_name_list=endpoint_name,
                    cluster_name=cluster.__class__.__name__,
                    attribute_name=attribute.Label,
                    is_readable=is_readable,
                    is_writable=is_writable
                )

    def _render_command(
            self,
            node_id: int,
            endpoint_id: int,
            endpoint_name: str,
            cluster: Cluster,
            command: type[ClusterCommand],
            feature: FeatureComponents) -> Optional[str]:
        """Renders a command into its OpenAPI yaml format"""
        jinja_template = env.get_template("commands.yml.j2")
        if jinja_template is None:
            return None
        if not feature.is_implemented(command.command_id):
            return None

        return jinja_template.render(
            node_id=node_id,
            endpoint_id=endpoint_id,
            endpoint_name_list=endpoint_name,
            cluster_name=cluster.__class__.__name__,
            command_name=command.__name__,
            has_body=len(command.descriptor.Fields) > 0,
            parameters={
                field.Label: self._convert_type(field.Type)
                for field in command.descriptor.Fields
            }
        )

    def _render_path_by_attributes(
            self,
            node_id: int,
            endpoint_id: int,
            endpoint_name: str,
            cluster: Cluster,
            feature: FeatureComponents) -> List[str]:
        """Renders the readable attributes of a cluster into its OpenAPI yaml format"""
        result = [
            self._render_attribute(
                node_id,
                endpoint_id,
                endpoint_name,
                cluster,
                attribute,
                feature)
            for attribute in cluster.descriptor.Fields
        ]
        return self._filter_not_none(result)

    def _render_path_by_commands(
            self,
            node_id: int,
            endpoint_id: int,
            endpoint_name: str,
            cluster: Cluster,
            feature: FeatureComponents) -> List[str]:
        """Renders the commands of a cluster into its OpenAPI yaml format"""
        result = [
            self._render_command(
                node_id,
                endpoint_id,
                endpoint_name,
                cluster,
                command,
                feature)
            for command in self._get_all_commands(cluster)
        ]
        return self._filter_not_none(result)

    def _render_path_by_cluster(
            self,
            node_id: int,
            endpoint_id: int,
            endpoint_name: str,
            cluster: Cluster) -> List[str]:
        """Renders a cluster into its OpenAPI yaml format"""
        feature = FeatureComponents()
        if not hasattr(cluster, 'id') or not hasattr(cluster, 'featureMap'):
            logging.info('The cluster %s has no id or featureMap',
                         cluster.__class__.__name__)
        else:
            feature_map = cluster.featureMap
            features = self.feature.get(cluster.id)
            if features is not None:
                feature = features.get_features_by_map(feature_map)

        rendered_attribute_list = self._render_path_by_attributes(
            node_id,
            endpoint_id,
            endpoint_name,
            cluster,
            feature
        )
        rendered_command_list = self._render_path_by_commands(
            node_id,
            endpoint_id,
            endpoint_name,
            cluster,
            feature
        )
        rendered_cluster_list = rendered_attribute_list + rendered_command_list
        return rendered_cluster_list

    def _render_path_by_endpoint(self, endpoint: MatterEndpoint) -> List[str]:
        """Renders an endpoint into its OpenAPI yaml format"""
        rendered_cluster_list = [
            self._render_path_by_cluster(
                node_id=endpoint.node.node_id,
                endpoint_id=endpoint.endpoint_id,
                endpoint_name=", ".join(
                    device_type.__name__
                    for device_type in endpoint.device_types
                ),
                cluster=cluster
            )
            for cluster in endpoint.clusters.values()
        ]
        rendered_cluster_list = self._flat_map(rendered_cluster_list)
        rendered_cluster_list = self._filter_not_none(rendered_cluster_list)
        return rendered_cluster_list

    def render_node(self, node: MatterNode) -> Optional[str]:
        """Renders a node into its OpenAPI yaml format"""
        rendered_endpoint_list = [
            self._render_path_by_endpoint(endpoint)
            for endpoint in node.endpoints.values()
        ]
        rendered_endpoint_list = self._flat_map(rendered_endpoint_list)
        rendered_endpoint_list = self._filter_not_none(rendered_endpoint_list)
        return None if len(rendered_endpoint_list) == 0 else "\n\n".join(rendered_endpoint_list)

    def _flat_map(self, list2d: List[List[T]]) -> List[T]:
        return [
            item
            for items in list2d
            for item in items
        ]

    def _filter_not_none(self, items: List[Optional[T]]) -> List[T]:
        return [item for item in items if item is not None]

    def _get_all_commands(self, cluster: Cluster):
        if not hasattr(cluster.__class__, 'Commands'):
            return []
        return [cmd_class for _, cmd_class in getmembers(
            cluster.__class__.Commands,
            lambda member: isclass(member) and issubclass(
                member, ClusterCommand)
        )]
