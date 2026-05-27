#!/usr/bin/env python
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_knowledge_json import (  # noqa: E402
    assign_bird_layout,
    assign_context_layout,
    assign_taxonomy_layout,
    build_graph,
    finalize_positions,
)


LABEL_BY_TYPE = {
    "bird": "Bird",
    "location": "Location",
    "habitat": "Habitat",
    "status": "Status",
    "threat": "Threat",
    "taxonomy": "Taxon",
}


def load_env_file() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def clean_properties(item: Dict[str, Any]) -> Dict[str, Any]:
    cleaned: Dict[str, Any] = {}
    for key, value in item.items():
        if value is None or value == "":
            continue
        if isinstance(value, list):
            compacted = [entry for entry in value if entry not in (None, "")]
            if not compacted:
                continue
            cleaned[key] = compacted
            continue
        if isinstance(value, (str, int, float, bool)):
            cleaned[key] = value
    return cleaned


def relation_type(relation: str) -> str:
    return "".join(char if char.isalnum() else "_" for char in relation.upper())


def batched(items: List[Dict[str, Any]], size: int) -> Iterable[List[Dict[str, Any]]]:
    for index in range(0, len(items), size):
        yield items[index : index + size]


class Neo4jHttp:
    def __init__(self, url: str, database: str, user: str, password: str) -> None:
        self.endpoint = f"{url.rstrip('/')}/db/{database}/tx/commit"
        token = base64.b64encode(f"{user}:{password}".encode("utf-8")).decode("ascii")
        self.headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
        }

    def run(self, statement: str, parameters: Dict[str, Any] | None = None) -> None:
        payload = json.dumps(
            {
                "statements": [
                    {
                        "statement": statement,
                        "parameters": parameters or {},
                    }
                ]
            }
        ).encode("utf-8")
        request = urllib.request.Request(self.endpoint, data=payload, headers=self.headers, method="POST")

        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"无法连接 Neo4j HTTP 接口: {exc}") from exc

        errors = body.get("errors") or []
        if errors:
            messages = "; ".join(f"{error.get('code')}: {error.get('message')}" for error in errors)
            raise RuntimeError(messages)


def prepare_graph() -> Dict[str, Any]:
    graph = build_graph()
    nodes = graph["nodes"]
    birds_by_id = {node_id: node for node_id, node in nodes.items() if node["type"] == "bird"}
    assign_taxonomy_layout(nodes, graph["taxonomy"])
    assign_bird_layout(nodes, birds_by_id, graph["taxonomy"])
    assign_context_layout(nodes, graph["links"])
    finalize_positions(nodes)
    return graph


def import_graph(client: Neo4jHttp, graph: Dict[str, Any], reset: bool, batch_size: int) -> None:
    nodes_by_label: defaultdict[str, List[Dict[str, Any]]] = defaultdict(list)
    for node in graph["nodes"].values():
        label = LABEL_BY_TYPE.get(node.get("type"))
        if not label:
            continue
        nodes_by_label[label].append(clean_properties(node))

    links_by_type: defaultdict[str, List[Dict[str, Any]]] = defaultdict(list)
    for link in graph["links"]:
        relation = link.get("relation", "")
        if not relation:
            continue
        rel_type = relation_type(relation)
        links_by_type[rel_type].append(clean_properties(link))

    if reset:
        print("清空 Neo4j 现有图数据...")
        client.run("MATCH (n) DETACH DELETE n")

    print("创建唯一约束...")
    client.run("CREATE CONSTRAINT graph_node_id IF NOT EXISTS FOR (n:GraphNode) REQUIRE n.id IS UNIQUE")
    for label in LABEL_BY_TYPE.values():
        client.run(f"CREATE CONSTRAINT {label.lower()}_id IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE")

    total_nodes = 0
    for label, rows in sorted(nodes_by_label.items()):
        for batch in batched(rows, batch_size):
            client.run(
                f"""
                UNWIND $rows AS row
                MERGE (n:GraphNode:{label} {{id: row.id}})
                SET n += row
                """,
                {"rows": batch},
            )
            total_nodes += len(batch)
        print(f"已导入节点 {label}: {len(rows)}")

    total_links = 0
    for rel_type, rows in sorted(links_by_type.items()):
        for batch in batched(rows, batch_size):
            client.run(
                f"""
                UNWIND $rows AS row
                MATCH (source:GraphNode {{id: row.source}})
                MATCH (target:GraphNode {{id: row.target}})
                MERGE (source)-[r:{rel_type} {{key: row.key}}]->(target)
                SET r += row
                """,
                {"rows": batch},
            )
            total_links += len(batch)
        print(f"已导入关系 {rel_type}: {len(rows)}")

    print(f"导入完成: {total_nodes} 个节点，{total_links} 条关系。")


def main() -> None:
    load_env_file()

    parser = argparse.ArgumentParser(description="Import bird graph CSV data into local Neo4j.")
    parser.add_argument("--no-reset", action="store_true", help="不清空现有 Neo4j 图数据，改为增量 MERGE。")
    parser.add_argument("--batch-size", type=int, default=500, help="每批写入 Neo4j 的行数。")
    args = parser.parse_args()

    url = os.environ.get("NEO4J_HTTP_URL", "http://localhost:7474")
    database = os.environ.get("NEO4J_DATABASE", "neo4j")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "birdneo4j123")

    started_at = time.time()
    print("构建内存图数据...")
    graph = prepare_graph()
    client = Neo4jHttp(url, database, user, password)
    import_graph(client, graph, reset=not args.no_reset, batch_size=max(50, args.batch_size))
    print(f"耗时 {time.time() - started_at:.1f}s")


if __name__ == "__main__":
    main()
