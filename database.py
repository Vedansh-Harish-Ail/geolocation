import json
from pathlib import Path


SEED_LOCATIONS = []
SEED_EDGES = []


def init_db(data_path: Path) -> None:
    data_path.parent.mkdir(parents=True, exist_ok=True)
    if data_path.exists():
        return

    payload = {
        "locations": [
            {
                "slug": slug,
                "name": name,
                "kind": kind,
                "floor": floor,
                "description": description,
            }
            for slug, name, kind, floor, description in SEED_LOCATIONS
        ],
        "edges": SEED_EDGES,
    }
    data_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_data(data_path: Path) -> dict:
    return json.loads(data_path.read_text(encoding="utf-8"))


def save_data(data_path: Path, data: dict) -> None:
    data_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_locations(data_path: Path) -> list[dict]:
    data = load_data(data_path)
    return sorted(data["locations"], key=lambda item: item["name"])


def get_location_by_slug(data_path: Path, slug: str) -> dict | None:
    for location in load_data(data_path)["locations"]:
        if location["slug"] == slug:
            return location
    return None


def get_graph(data_path: Path) -> dict[str, dict]:
    locations = {location["slug"]: location for location in get_locations(data_path)}
    graph = {
        slug: {
            "location": data,
            "neighbors": [],
        }
        for slug, data in locations.items()
    }

    for edge in load_data(data_path)["edges"]:
        graph[edge["from"]]["neighbors"].append({
            "to": edge["to"],
            "distance": edge["distance"],
            "type": edge.get("type", "way"),
            "is_accessible": edge.get("is_accessible", True)
        })
        graph[edge["to"]]["neighbors"].append({
            "to": edge["from"],
            "distance": edge["distance"],
            "type": edge.get("type", "way"),
            "is_accessible": edge.get("is_accessible", True)
        })

    return graph


def get_edges(data_path: Path) -> list[dict]:
    return load_data(data_path)["edges"]


def update_data(data_path: Path, locations: list[dict], edges: list[dict]) -> None:
    payload = {
        "locations": locations,
        "edges": edges,
    }
    save_data(data_path, payload)
