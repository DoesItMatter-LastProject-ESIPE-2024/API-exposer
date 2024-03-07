"""Convert matter objects into yaml"""

from dataclasses import dataclass
import json
import logging
from inspect import isclass, getmembers
from typing import Dict, Optional, List, _GenericAlias, Set
from jinja2 import Environment, FileSystemLoader, select_autoescape
from matter_server.client.models.node import MatterNode, MatterEndpoint
from chip.clusters.ClusterObjects import Cluster, ClusterObjectFieldDescriptor, ClusterCommand

from api_exposer.const import SWAGGER_PATHS_TEMPLATE_FOLDER
from api_exposer.feature import Features, NamedId


env = Environment(
    loader=FileSystemLoader(SWAGGER_PATHS_TEMPLATE_FOLDER),
    autoescape=select_autoescape()
)


@dataclass
class Convertor:
    """TODO"""
    feature: Dict[int, Features]

    def _convert_type(self, class_type: type) -> str:
        match class_type:
            case _GenericAlias(): return 'null'
            case [list(), set()]: return 'null'
            case dict(): return 'null'
            case integer if issubclass(integer, int): return 'integer'
            case string if issubclass(string, str): return 'string'
            case _: return 'null'

    def _render_attribute(self, node_id: int, endpoint_id: int, endpoint_name: str, cluster: Cluster, attribute: ClusterObjectFieldDescriptor, is_readable: bool, is_writable: bool) -> Optional[str]:
        """Renders an attribute path into its OpenAPI yaml format"""
        jinja_template = env.get_template("attributes.yml.j2")
        return None if jinja_template is None else jinja_template.render(
            node_id=node_id,
            endpoint_id=endpoint_id,
            endpoint_name_list=endpoint_name,
            cluster_name=cluster.__class__.__name__,
            attribute_name=attribute.Label,
            is_readable=is_readable,
            is_writable=is_writable
        )

    def _render_command(self, node_id: int, endpoint_id: int, endpoint_name: str, cluster: Cluster, command: type[ClusterCommand]) -> Optional[str]:
        """Renders a command into its OpenAPI yaml format"""
        jinja_template = env.get_template("commands.yml.j2")
        return None if jinja_template is None else jinja_template.render(
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

    def _is_attribute_readable_or_writable(self, attribute: ClusterObjectFieldDescriptor, unreadable_attribute_list: Set[NamedId], unwritable_attribute_list: Set[NamedId]) -> List[bool]:
        result = []
        result.append(not any(attribute.Tag ==
                      named_id.id for named_id in unreadable_attribute_list))
        result.append(not any(attribute.Tag ==
                      named_id.id for named_id in unwritable_attribute_list))
        print(result)
        return result

    def _render_path_by_attributes(self, node_id: int, endpoint_id: int, endpoint_name: str, cluster: Cluster, unreadable_attribute_list: Set[NamedId], unwritable_attribute_list: Set[NamedId]) -> List[str]:
        """Renders the readable attributes of a cluster into its OpenAPI yaml format"""
        rendered_attribute_list = []
        for attribute in cluster.descriptor.Fields:
            match (self._is_attribute_readable_or_writable(attribute, unreadable_attribute_list, unwritable_attribute_list)):
                case [False, False]:  # Neither get or post
                    pass
                case [is_readable, is_writable]:
                    rendered_attribute_list.append(
                        self._render_attribute(
                            node_id, endpoint_id, endpoint_name, cluster, attribute, is_readable, is_writable)
                    )
                case _:
                    logging.warning("TODO")

        rendered_attribute_list = [
            rendered_attribute for rendered_attribute in rendered_attribute_list
            if rendered_attribute is not None
        ]
        return rendered_attribute_list

    def _render_path_by_commands(self, node_id: int, endpoint_id: int, endpoint_name: str, cluster: Cluster, unimplemented_command_list: Set[NamedId]) -> List[str]:
        """Renders the commands of a cluster into its OpenAPI yaml format"""
        rendered_command_list = [
            self._render_command(
                node_id,
                endpoint_id,
                endpoint_name,
                cluster,
                command
            )
            for command in self._get_all_commands(cluster)
            if not any(command.command_id == named_id.id for named_id in unimplemented_command_list)
        ]

        rendered_command_list = [
            rendered_attribute
            for rendered_attribute in rendered_command_list
            if rendered_attribute is not None
        ]
        return rendered_command_list

    def _render_path_by_cluster(self, node_id: int, endpoint_id: int, endpoint_name: str, cluster: Cluster) -> List[str]:
        """Renders a cluster into its OpenAPI yaml format"""
        unreadable_attribute_list = []
        unwritable_attribute_list = []
        unimplemented_command_list = []
        if not hasattr(cluster, 'id') or not hasattr(cluster, 'featureMap'):
            print("This cluster has no id or featureMap")
        else:
            feature_map = cluster.featureMap
            features = self.feature.get(cluster.id)
            if (features is not None):
                feature_components = features.get_features_by_map(feature_map)
                # if (feature_components is not None) :
                unreadable_attribute_list = feature_components.not_readable_attributes
                unwritable_attribute_list = feature_components.not_writable_attributes
                unimplemented_command_list = feature_components.not_implemented_commands

        rendered_attribute_list = self._render_path_by_attributes(
            node_id,
            endpoint_id,
            endpoint_name,
            cluster,
            unreadable_attribute_list,
            unwritable_attribute_list
        )
        rendered_command_list = self._render_path_by_commands(
            node_id,
            endpoint_id,
            endpoint_name,
            cluster,
            unimplemented_command_list
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
        rendered_cluster_list = [
            rendered_cluster for rendered_cluster in rendered_cluster_list
            if rendered_cluster is not None
        ]
        return rendered_cluster_list

    def render_node(self, node: MatterNode) -> Optional[str]:
        """Renders a node into its OpenAPI yaml format"""
        rendered_endpoint_list = [
            self._render_path_by_endpoint(endpoint)
            for endpoint in node.endpoints.values()
        ]
        rendered_endpoint_list = self._flat_map(rendered_endpoint_list)
        rendered_endpoint_list = [
            rendered_endpoint
            for rendered_endpoint in rendered_endpoint_list
            if rendered_endpoint is not None
        ]
        return None if len(rendered_endpoint_list) == 0 else "\n\n".join(rendered_endpoint_list)

    def _flat_map(self, list2d: List[List[str]]) -> List[str]:
        return [
            item
            for items in list2d
            for item in items
        ]

    def _get_all_commands(self, cluster: Cluster):
        if not hasattr(cluster.__class__, 'Commands'):
            return []
        return [cmd_class for _, cmd_class in getmembers(
            cluster.__class__.Commands,
            lambda member: isclass(member) and issubclass(
                member, ClusterCommand)
        )]
