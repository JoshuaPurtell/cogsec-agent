from pydantic import BaseModel
import networkx as nx
from enum import Enum
from typing import List
from dataclasses import dataclass
from collections import deque
import json

class NodeType(str, Enum):
    CLAIM = "Claim"
    EVIDENCE = "Evidence"
    EXAMPLE = "Example"

class EdgeType(str, Enum):
    SUPPORTS = "Supports"
    REFUTES = "Refutes"
    SUGGESTS = "Suggests"

def local_graph_sort(graph, special_nodes, node, direction='downstream'):
    """
    Get the subgraph either upstream or downstream of a special node, excluding other special nodes
    and any nodes upstream/downstream of them, respectively.

    Parameters:
    - graph: NetworkX DiGraph
    - special_nodes: set of special nodes
    - node: the special node to start from
    - direction: either 'downstream' or 'upstream'

    Returns:
    - A subgraph containing the nodes and edges in the subgraph
    """
    if direction not in {'upstream', 'downstream'}:
        raise ValueError("Direction must be 'upstream' or 'downstream'")
    
    if direction == 'upstream':
        graph = graph.reverse()

    queue = deque([node])
    visited = set([node])
    subgraph_nodes = set()
    subgraph_edges = set()
    
    while queue:
        current_node = queue.popleft()
        neighbors = list(graph.successors(current_node))
        for neighbor in neighbors:
            edge_type = graph[current_node][neighbor]["edge_type"]
            if neighbor not in visited and neighbor not in special_nodes:
                visited.add(neighbor)
                queue.append(neighbor)
                subgraph_nodes.add(neighbor)
                subgraph_edges.add((current_node, neighbor, edge_type))
            else:
                if neighbor in special_nodes:
                    visited.add(neighbor)
                    subgraph_nodes.add(neighbor)
                    subgraph_edges.add((current_node, neighbor, edge_type))
    
    subgraph = nx.DiGraph()
    subgraph.add_nodes_from(subgraph_nodes)
    for source, target, edge_type in subgraph_edges:
        subgraph.add_edge(source, target, edge_type=edge_type)
    return subgraph

def print_subgraph(subgraph, direction='downstream'):
    readout = []
    for directed_edge in subgraph.edges():
        edge_type = subgraph[directed_edge[0]][directed_edge[1]]["edge_type"]
        if direction == 'upstream':
            readout.append(f"||{directed_edge[1]}|| -> || {edge_type} || -> ||{directed_edge[0]}||")
        else:
            readout.append(f"||{directed_edge[0]}|| -> || {edge_type} || -> ||{directed_edge[1]}||")
    return readout

@dataclass
class ArgumentGraph:
    G: nx.DiGraph
    important_nodes_ordered: List[str]
    oevre: str

    def load_from_json(self, path):
        with open(path, 'r') as f:
            json_data = json.load(f)
            self.from_json(json_data)

    def to_json(self):
        return {
            "graph": nx.node_link_data(self.G),
            "important_nodes_ordered": self.important_nodes_ordered,
            "oevre": self.oevre
        }
    
    def from_json(self, json_data):
        self.G = nx.node_link_graph(json_data["graph"])
        self.important_nodes_ordered = json_data["important_nodes_ordered"]
        self.oevre = json_data["oevre"]

    def add_node(self, node_id: str, node_type: NodeType):
        self.G.add_node(node_id, node_type=node_type)
    
    def add_edge(self, source: str, target: str, edge_type: EdgeType):
        self.G.add_edge(source, target, edge_type=edge_type)

    def load_from_nodes_and_edges(self, nodes, edges):
        for node in nodes:
            self.add_node(node["id"], NodeType[node["type_value"]])
        for edge in edges:
            self.add_edge(edge["source"], edge["target"], EdgeType[edge["type_value"]])
    
    def traverse_graph(self):
        argument_chunks = []
        for node in self.important_nodes_ordered:
            upstream_subgraph = local_graph_sort(self.G, set(self.important_nodes_ordered), node, direction='upstream')
            downstream_subgraph = local_graph_sort(self.G, set(self.important_nodes_ordered), node, direction='downstream')
            argument_chunks.append(
                print_subgraph(upstream_subgraph, direction="upstream") + print_subgraph(downstream_subgraph, direction="downstream")
            )
        return argument_chunks

if __name__ == "__main__":
    G = nx.DiGraph()
    arg_graph = ArgumentGraph(G=G, important_nodes_ordered=[], oevre="")
    arg_graph.add_node("A", NodeType.CLAIM)
    arg_graph.add_node("aa", NodeType.EVIDENCE)
    arg_graph.add_node("ab", NodeType.EVIDENCE)
    arg_graph.add_node("B", NodeType.CLAIM)
    arg_graph.add_node("C", NodeType.CLAIM)
    arg_graph.add_edge("A", "B", EdgeType.SUPPORTS)
    arg_graph.add_edge("aa", "A", EdgeType.SUPPORTS)
    arg_graph.add_edge("ab", "A", EdgeType.SUPPORTS)
    arg_graph.add_edge("B", "C", EdgeType.REFUTES)
    arg_graph.important_nodes_ordered = ["A", "B", "C"]
    arg_graph.oevre = "This is a test"
    print(arg_graph.traverse_graph())
