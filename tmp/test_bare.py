import json, time, sys
from pathlib import Path
import numpy as np
import jieba
from rank_bm25 import BM25Okapi

ROOT = Path('.').resolve()

print('load npz...', flush=True)
data = np.load(str(ROOT / 'public' / 'data' / 'embeddings.npz'), allow_pickle=True)
print(f'emb shape: {data["embeddings"].shape}', flush=True)

with open(ROOT / 'public' / 'data' / 'embeddings_meta.json', 'r', encoding='utf-8') as f:
    meta = json.load(f)
print(f'meta count: {meta["count"]}', flush=True)

names = meta.get('names', [])
print(f'building bm25 for {len(names)} items...', flush=True)
corpus = []
for i, name in enumerate(names):
    tokens = list(jieba.cut((name or '').lower()))
    corpus.append(tokens)
bm25 = BM25Okapi(corpus)
print(f'bm25 done: {len(corpus)} docs', flush=True)

# taxonomy from graph_preview
gp_path = ROOT / 'public' / 'data' / 'graph_preview.json'
print(f'reading graph_preview...', flush=True)
t0 = time.time()
with open(str(gp_path), 'r', encoding='utf-8-sig') as f:
    gp = json.load(f)
print(f'gp: {len(gp.get("nodes",[]))} nodes, {len(gp.get("links",[]))} links in {time.time()-t0:.1f}s', flush=True)

print('ALL DONE', flush=True)
