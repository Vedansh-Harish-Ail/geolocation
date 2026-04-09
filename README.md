# Smart Campus Navigation System

A starter Flask application for QR-based campus navigation using graph routing.

## Features

- QR-style entry points using `/qr/<location-slug>`
- Manual source and destination selection
- Dijkstra shortest-path routing on a campus graph
- File-backed campus graph seed data that can be migrated to SQLite
- Simple Leaflet campus map visualization
- JSON APIs for locations and route data

## Run locally

1. Create a virtual environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Start the app:

```powershell
python app.py
```

4. Open `http://127.0.0.1:5000`

## Example QR entry URLs

- `http://127.0.0.1:5000/qr/main-gate`
- `http://127.0.0.1:5000/qr/library`
- `http://127.0.0.1:5000/qr/lab-complex`

## Next improvements

- Replace the starter grid map with a real campus floorplan or site image
- Add QR image generation for each location
- Add admin management for locations and path updates
- Move the data layer to SQLite when the local environment supports database writes
- Support multi-floor routing and accessibility-aware paths
