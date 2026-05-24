"""Resolve birds.csv git merge conflict by keeping HEAD (richer taxonomy schema)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
birds_path = ROOT / "data" / "birds.csv"
text = birds_path.read_text(encoding="utf-8-sig")

if "<<<<<<< HEAD" not in text:
    print("No merge conflict markers found; nothing to do.")
    raise SystemExit(0)

head, rest = text.split("<<<<<<< HEAD\n", 1)[1].split("\n=======\n", 1)
incoming = rest.split("\n>>>>>>>", 1)[0]

resolved = head.strip().lstrip("\ufeff") + "\n"
if resolved.startswith("id,"):
    pass
else:
    resolved = resolved.replace("\ufeffid,", "id,", 1)
birds_path.write_text(resolved, encoding="utf-8")

head_lines = len(head.strip().splitlines()) - 1
incoming_lines = len(incoming.strip().splitlines()) - 1
print(f"Resolved birds.csv: kept HEAD ({head_lines} rows), discarded incoming ({incoming_lines} rows)")
