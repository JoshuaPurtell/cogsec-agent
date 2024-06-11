# Essay Deconstruction Pipeline
# - Currently designed for short essays
# - Hence, not much of a 'pipeline' yet
# =============================
from typing import List
import asyncio
import json
import networkx as nx
from pydantic import BaseModel
from src.lms.oai import async_openai_chat_completion, async_openai_chat_completion_with_response_model
from src.pipelines.ontology import NodeType, EdgeType, ArgumentGraph

class Node(BaseModel):
    type: NodeType
    content: str

class Edge(BaseModel):
    type: EdgeType
    source: Node
    target: Node

class DeconstructedEssayGraphResponse(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
    important_nodes_ordered: List[str]
    oevre: str

def deconstruct(essay: str) -> ArgumentGraph:
    system_prompt = """
# Premise
A deconstructed essay graph is a directed graph where nodes represent:
- Claims
- Pieces of Evidence
- Examples

and edges represent the relationships between these nodes, namely:
- Supports
- Refutes
- Suggests (motivates, but does not logically entail)

It also specifies an ordered list of the most important claims in the essay, and the ouvre of the essay.

# Instructions
Please deconstruct the following essay into a directed graph.
- Each node should be a claim, piece of evidence, or example. Each node should be reduced to its essence, in one or two sentences.
- Each edge should be a relationship between two nodes, either supporting, refuting, or suggesting.
- The ouvre should be a single sentence indicating the style or mood of the essay.
- The important claims should be provided in the order they appear in the essay. Each important claim must be a node in the graph.

Please be as concise as possible, and do not include any extraneous information.
"""
    user_prompt = f"""# The Essay\n{essay}\n\n Your deconstruction:"""
    messages = [{"role":"system","content": system_prompt},{"role":"user","content": user_prompt}]
    result: DeconstructedEssayGraphResponse = asyncio.run(async_openai_chat_completion_with_response_model(messages=messages, model="gpt-3.5-turbo", response_model=DeconstructedEssayGraphResponse, max_tokens=3000))
    arg_graph = ArgumentGraph(G=nx.DiGraph(), important_nodes_ordered=result.important_nodes_ordered, oevre=result.oevre)
    arg_graph.load_from_nodes_and_edges([{
        "id": node.content,
        "type_value": node.type
    } for node in result.nodes], [{
        "source": edge.source.content,
        "target": edge.target.content,
        "type_value": edge.type
    } for edge in result.edges])
    return arg_graph

if __name__ == "__main__":
    #result = asyncio.run(async_openai_chat_completion(messages=[{"role":"user","content": "The quick brown fox jumps over the lazy dog"}]))
    praxis_essay = """
Man is not the apex predator. Instead, his time, energy, [agency](https://joshpurtell.substack.com/p/are-you-serious-draft) and life-force more broadly are parasitized by self-replicating memeplexes - a.k.a egregores. [Egregores](https://joshpurtell.substack.com/p/cognitive-cybersecurity-draft) are an inevitability: given that ideas can manipulate emotions and distort our perception of reality, there will _always_ from the recombinant soup of social intercourse emerge certain specimens that do so in order to spread themselves [FN - this also suggests that egregores will infect LLMs - more on that later]. Language is our Genesis serpent - it offers knowledge and yet _necessarily_ also subjugation and enslavement. It helped to propel us out of trophic subjugation by snakes, eagles, and lions and into trophic subjugation by ideologies, narcissistic delusion, and sociological paroxysms.

[Julian Jaynes](https://en.wikipedia.org/wiki/The_Origin_of_Consciousness_in_the_Breakdown_of_the_Bicameral_Mind) suggests that rising complexity in the Near East precipitated the rise of consciousness - but doesn't suggest why (he handwaves at stress). I suggest that the self, and consciousness more broadly, was one of many psycho-technologies man invented to cope with the explosion of economic and social complexity (and therefore egregores) that followed the development of militarism c. ~ 1800 BC and thereafter, the empire. 

Before the development of militarism, and, specifically, the chariot, civilization amounted to individual cities small enough to enclose in an earthen mound - or less. Social stratification mostly amounted to kings and peasants. 

Then chariots were invented, for which warrior and artisan classes were organized and with which civilization expanded to scales of tens of millions of souls. 
"""
    arg_graph = deconstruct(praxis_essay)
    with open("temp/praxis_essay.json", "w") as f:
        f.write(json.dumps(arg_graph.to_json()))