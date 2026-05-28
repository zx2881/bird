import json, sys
sys.path.insert(0, 'scripts')
from search_server import load_data, load_node_chunk, expand_graph
load_data()

chunk = load_node_chunk('bird-red-crowned-crane')
print(f'Chunk: {chunk is not None}')
if chunk:
    print(f'Nodes: {len(chunk.get("nodes",[]))}, Links: {len(chunk.get("links",[]))}')
related = expand_graph('bird-red-crowned-crane', max_hops=1)
print(f'Expanded: {len(related)}')
for r in related[:5]:
    print(f'  {r["name"]} [{r["type"]}] via {r["relationLabel"]} from {r["viaName"]}')
