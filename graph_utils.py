import heapq


def dijkstra_shortest_path(
    graph: dict,
    source: str,
    destination: str,
    filters: dict | None = None
) -> tuple[list[str], float]:
    filters = filters or {}
    distances = {node: float("inf") for node in graph}
    previous = {node: None for node in graph}
    distances[source] = 0

    queue = [(0, source)]
    while queue:
        current_distance, current_node = heapq.heappop(queue)
        if current_node == destination:
            break

        if current_distance > distances[current_node]:
            continue

        for edge in graph[current_node]["neighbors"]:
            neighbor = edge["to"]
            weight = edge["distance"]

            # ─── Filter Logic ───
            if filters.get("avoid_stairs") and edge.get("type") == "stairs":
                continue
            if filters.get("accessible_only") and not edge.get("is_accessible"):
                continue

            candidate = current_distance + weight
            if candidate < distances[neighbor]:
                distances[neighbor] = candidate
                previous[neighbor] = current_node
                heapq.heappush(queue, (candidate, neighbor))

    if distances[destination] == float("inf"):
        return [], float("inf")

    path = []
    current = destination
    while current is not None:
        path.append(current)
        current = previous[current]
    path.reverse()
    return path, distances[destination]


def build_route_details(path: list[str], graph: dict) -> list[dict]:
    if not path:
        return []

    details = []
    for index, slug in enumerate(path):
        location = graph[slug]["location"]
        entry = {
            "slug": slug,
            "name": location["name"],
            "description": location["description"],
            "floor": location.get("floor", "1"),
            "segment_distance": 0,
            "instruction": "Start here" if index == 0 else "Proceed here",
        }
        if index > 0:
            previous_slug = path[index - 1]
            # Find the specific edge that connected them
            edge = next((e for e in graph[previous_slug]["neighbors"] if e["to"] == slug), None)
            if edge:
                entry["segment_distance"] = edge["distance"]
                if edge["type"] == "stairs":
                    entry["instruction"] = "Take the stairs to"
                elif edge["type"] == "elevator":
                    entry["instruction"] = "Take the elevator to"

        if index == len(path) - 1:
            entry["instruction"] = "Destination reached"
        details.append(entry)
    return details
