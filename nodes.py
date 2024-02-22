""" 
===================== nodes.py =====================
contain Nodes class for API-EXPOSER
"""
import logging
import asyncio
from asyncio import Event

from typing import Dict
from threading import Thread
from aiohttp import ClientSession

from matter_server.common.models import EventType
from matter_server.client.client import MatterClient
from matter_server.client.models.node import MatterNode


class Nodes:
    """ 
    =============== class nodes ===============
    class to create a client, connect to Matter
    Fabric and get all nodes
    """

    def __init__(self, url: str):
        self.url: str = url
        self.nodes: Dict[int, MatterNode] = {}
        self.client_global: MatterClient | None = None
        self.wait_listening: Event = Event()

    def _handle_node_added(self, node: MatterNode):
        self.nodes[node.node_id] = node
        logging.info("node %d added %s", node.node_id, node)

    def _handle_node_updated(self, node: MatterNode):
        logging.info("node %d updated %s", node.node_id, node)
        self.nodes[node.node_id] = node

    def _handle_node_removed(self, node_id: int):
        removed = self.nodes.pop(node_id)
        logging.info("node %d added %s", node_id, removed)

    def _handle_event(self, event: EventType, *args):
        match event:
            case EventType.NODE_ADDED:
                self._handle_node_added(*args)
            case EventType.NODE_UPDATED:
                self._handle_node_updated(*args)
            case EventType.NODE_REMOVED:
                self._handle_node_removed(*args)
            case _:
                pass

    async def _run_client(self):
        async with ClientSession() as session:
            async with MatterClient(self.url, session) as client:
                self.client_global = client
                client.subscribe_events(self._handle_event)

                # start listening
                await client.start_listening(self.wait_listening)

    def _get_nodes(self):
        Thread(target=asyncio.run, args=[self.wait_listening.wait()]).run()

        self.nodes.update(
            {node.node_id: node for node in self.client_global.get_nodes()})
        logging.info(self.nodes)

    def run(self):
        """connect to Serveur and get matter nodes list"""
        thread = Thread(target=asyncio.run, args=[self._run_client()])
        thread.start()
        self._get_nodes()
        thread.join()
