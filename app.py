from collections import Counter
from functools import wraps
from pathlib import Path

from flask import (
    Flask, abort, flash, jsonify, redirect,
    render_template, request, session, url_for,
    send_from_directory
)
import qrcode
import os

from database import (
    get_edges, get_graph, get_location_by_slug,
    get_locations, init_db, save_data, update_data,
)
from demo_content import (
    LANDING_HIGHLIGHTS,
    LANDING_METRICS,
    ASSET_METRICS,
    ASSET_STATUS_SEGMENTS,
    ASSET_INVENTORY,
    SECURITY_ALERTS,
    SAFETY_PROTOCOLS,
    SAFETY_EVENTS,
    PANIC_TRIGGERS,
    SAFETY_HEAT_ZONES,
    BEACON_INVENTORY,
    FIRMWARE_STATUS,
    DIRECTORY_SECTIONS,
    DIRECTORY_ENTRIES,
)
from graph_utils import build_route_details, dijkstra_shortest_path


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "campus_graph.json"

app = Flask(__name__)
app.secret_key = "campus-nav-secret-2025-change-in-prod"
app.config["DATA_PATH"] = DATA_PATH

# ─── Admin credentials (change before deployment) ───────────────────────────
APP_NAME = "Campus Nav"
COLLEGE_NAME = "Your University"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password2025"

with app.app_context():
    init_db(DATA_PATH)


# ─── Auth decorator ──────────────────────────────────────────────────────────
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


# ─── QR Utility ──────────────────────────────────────────────────────────────
def generate_qr(slug: str):
    """Generates a QR code for a location and saves it to static/qrcodes."""
    qr_dir = BASE_DIR / "static" / "qrcodes"
    qr_dir.mkdir(parents=True, exist_ok=True)
    
    # Construct the URL. Using request.host_url to get the current server address.
    target_url = f"{request.host_url.rstrip('/')}/qr/{slug}"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(target_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_path = qr_dir / f"{slug}.png"
    img.save(str(img_path))
    return f"qrcodes/{slug}.png"


def build_operations_dashboard_context() -> dict:
    locations = get_locations(DATA_PATH)
    edges = get_edges(DATA_PATH)

    location_kinds = Counter((loc.get("kind") or "Other") for loc in locations)
    accessible_edges = sum(1 for edge in edges if edge.get("is_accessible"))
    accessibility_rate = round((accessible_edges / len(edges)) * 100) if edges else 0

    breakdown_rows = [
        {
            "name": kind,
            "count": count,
            "share": round((count / len(locations)) * 100) if locations else 0,
            "status": "Active" if count else "Planned",
            "note": "Live from current campus graph",
        }
        for kind, count in sorted(location_kinds.items(), key=lambda item: (-item[1], item[0]))
    ]

    if not breakdown_rows:
        breakdown_rows = [
            {
                "name": "No segments yet",
                "count": 0,
                "share": 0,
                "status": "Planned",
                "note": "Add locations to populate this table",
            }
        ]

    trend_axis = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    trend_series = [
        {
            "label": "Traffic",
            "value": f"{max(1, len(locations) * 6)} visits",
            "delta": "+12% assumption",
            "tone": "blue",
            "detail": "Placeholder weekly trend until visit telemetry is stored.",
        },
        {
            "label": "Incidents",
            "value": f"{max(0, len(edges) - accessible_edges)} flags",
            "delta": "Needs event feed",
            "tone": "red",
            "detail": "Derived placeholder based on current graph coverage gaps.",
        },
    ]

    kpis = [
        {
            "label": "Mapped locations",
            "value": str(len(locations)),
            "detail": "Live from campus graph",
        },
        {
            "label": "Route connections",
            "value": str(len(edges)),
            "detail": "Live graph edges",
        },
        {
            "label": "Accessible coverage",
            "value": f"{accessibility_rate}%",
            "detail": "Accessible edges / total edges",
        },
        {
            "label": "Largest segment",
            "value": breakdown_rows[0]["name"],
            "detail": "Top location category today",
        },
    ]

    return {
        "console_title": "Operations Dashboard",
        "console_subtitle": "Extensible overview shell for campus KPIs, trends, and category breakdowns",
        "active_console": "overview",
        "console_theme": "console-dark",
        "kpis": kpis,
        "trend_axis": trend_axis,
        "trend_series": trend_series,
        "breakdown_rows": breakdown_rows,
        "assumptions": [
            "KPIs use live campus graph data from locations and edges.",
            "Trend cards are placeholders until time-series analytics are stored.",
            "Breakdown table groups locations by the existing 'kind' field.",
        ],
    }


# ═══════════════════════════════════════ PUBLIC ROUTES ══════════════════════

@app.get("/qr/<slug>")
def qr_entry(slug: str):
    """Handler for QR code scans. Sets the source and redirects to planner."""
    location = get_location_by_slug(DATA_PATH, slug)
    if not location:
        abort(404, "Location not found.")
    return redirect(url_for("planner_view", source=slug))


@app.get("/")
def index():
    locations = get_locations(DATA_PATH)
    return render_template(
        "index.html",
        locations=locations,
        highlights=LANDING_HIGHLIGHTS,
        metrics=LANDING_METRICS,
        active_page="home",
    )


@app.post("/route")
def route_redirect():
    source = request.form.get("source", "").strip().lower()
    destination = request.form.get("destination", "").strip().lower()
    query = {}
    if source:
        query["source"] = source
    if destination:
        query["destination"] = destination

    # Pass accessibility filters
    for key in ["use_elevators", "avoid_stairs", "accessible_only", "avoid_crowds"]:
        val = request.form.get(key)
        if val:
            query[key] = val

    return redirect(url_for("planner_view", **query))


def build_planner_context(source_slug: str, destination_slug: str, filters: dict = None) -> dict:
    locations = get_locations(DATA_PATH)
    edges = get_edges(DATA_PATH)
    source = get_location_by_slug(DATA_PATH, source_slug) if source_slug else None
    destination = get_location_by_slug(DATA_PATH, destination_slug) if destination_slug else None

    if source_slug and source is None:
        abort(404, "Unknown source location.")
    if destination_slug and destination is None:
        abort(404, "Unknown destination.")

    path_slugs = []
    total_distance = None
    walk_minutes = None
    route_details = []
    route_error = None

    if source and destination:
        graph = get_graph(DATA_PATH)
        path_slugs, total_distance = dijkstra_shortest_path(graph, source_slug, destination_slug, filters)
        route_details = build_route_details(path_slugs, graph)
        if path_slugs:
            walk_minutes = max(1, round(total_distance / 70))
        else:
            route_error = "No route could be generated with the selected accessibility options."

    quick_links = [
        loc for loc in locations
        if loc["slug"] in {"central-library", "deanery-office", "canteen", "auditorium"}
    ]
    return {
        "locations": locations,
        "edges": edges,
        "source": source,
        "destination": destination,
        "path_slugs": path_slugs,
        "total_distance": total_distance,
        "walk_minutes": walk_minutes,
        "route_details": route_details,
        "route_error": route_error,
        "quick_links": quick_links,
        "active_page": "planner",
    }


@app.get("/planner")
@app.get("/route")
def planner_view():
    source_slug = request.args.get("source", "").strip().lower()
    destination_slug = request.args.get("destination", "").strip().lower()

    filters = {
        "use_elevators": request.args.get("use_elevators") == "on",
        "avoid_stairs": request.args.get("avoid_stairs") == "on",
        "accessible_only": request.args.get("accessible_only") == "on",
        "avoid_crowds": request.args.get("avoid_crowds") == "on",
    }

    return render_template("route.html", **build_planner_context(source_slug, destination_slug, filters))


# ═══════════════════════════════════════ ADMIN ROUTES ═══════════════════════

@app.get("/admin/login")
@app.post("/admin/login")
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            session["admin_user"] = username
            flash("Welcome back, " + username + "!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            error = "Invalid username or password. Please try again."

    return render_template("admin_login.html", error=error)


@app.get("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.get("/admin")
@app.get("/admin/dashboard")
@admin_required
def admin_dashboard():
    locations = get_locations(DATA_PATH)
    edges = get_edges(DATA_PATH)
    return render_template(
        "admin_dashboard.html",
        locations=locations,
        edges=edges,
        admin_tab="overview",
        admin_username=ADMIN_USERNAME,
        active_page="admin",
    )


@app.get("/admin/locations")
@admin_required
def admin_locations():
    locations = get_locations(DATA_PATH)
    edges = get_edges(DATA_PATH)
    return render_template(
        "admin_dashboard.html",
        locations=locations,
        edges=edges,
        admin_tab="locations",
        admin_username=ADMIN_USERNAME,
        active_page="admin",
    )


@app.get("/admin/locations/new")
@admin_required
def admin_new_location():
    locations = get_locations(DATA_PATH)
    return render_template("admin_add_location.html", 
                         locations=locations, 
                         active_page="admin")


@app.post("/admin/locations/add")
@admin_required
def admin_add_location():
    name = request.form.get("name", "").strip()
    slug = request.form.get("slug", "").strip().lower()
    kind = request.form.get("kind", "Other").strip()
    floor = request.form.get("floor", "1").strip()
    desc = request.form.get("description", "").strip()
    image_url = request.form.get("image_url", "").strip()

    if not name or not slug:
        flash("Name and slug are required.", "danger")
        return redirect(url_for("admin_dashboard"))

    locations = get_locations(DATA_PATH)
    edges = get_edges(DATA_PATH)


    if any(l["slug"] == slug for l in locations):
        flash(f"Slug '{slug}' already exists.", "danger")
        return redirect(url_for("admin_dashboard"))

    # Save new location
    new_loc = {
        "slug": slug, "name": name, "kind": kind,
        "floor": floor, "description": desc,
        "image_url": image_url
    }
    locations.append(new_loc)

    update_data(DATA_PATH, locations, edges)
    
    # Generate QR Code automatically
    try:
        generate_qr(slug)
        flash(f"Location '{name}' added and QR code generated.", "success")
    except Exception as e:
        flash(f"Location '{name}' added, but QR generation failed: {str(e)}", "warning")
        
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/locations/delete/<slug>")
@admin_required
def admin_delete_location(slug: str):
    locations = [l for l in get_locations(DATA_PATH) if l["slug"] != slug]
    edges = [e for e in get_edges(DATA_PATH) if e["from"] != slug and e["to"] != slug]
    update_data(DATA_PATH, locations, edges)
    flash("Location removed.", "success")
    return redirect(url_for("admin_locations"))


@app.get("/admin/qr-codes")
@admin_required
def admin_qr_codes():
    locations = get_locations(DATA_PATH)
    edges = get_edges(DATA_PATH)
    return render_template(
        "admin_dashboard.html",
        locations=locations,
        edges=edges,
        admin_tab="qrcodes",
        admin_username=ADMIN_USERNAME,
        active_page="admin",
    )


@app.get("/admin/routes")
@admin_required
def admin_routes():
    locations = get_locations(DATA_PATH)
    edges = get_edges(DATA_PATH)
    return render_template(
        "admin_dashboard.html",
        locations=locations,
        edges=edges,
        admin_tab="routes",
        admin_username=ADMIN_USERNAME,
        active_page="admin",
    )


@app.get("/admin/routes/new")
@admin_required
def admin_new_route():
    locations = get_locations(DATA_PATH)
    return render_template("admin_add_route.html", locations=locations, active_page="admin")


@app.post("/admin/routes/add")
@admin_required
def admin_add_route():
    from_slug = request.form.get("from_slug")
    to_slug = request.form.get("to_slug")
    distance = int(request.form.get("distance", 10))
    kind = request.form.get("type", "way")
    accessible = request.form.get("is_accessible") == "on"

    if from_slug == to_slug:
        flash("Cannot connect a location to itself.", "danger")
        return redirect(url_for("admin_new_route"))

    locations = get_locations(DATA_PATH)
    edges = get_edges(DATA_PATH)

    from_loc = next((l for l in locations if l["slug"] == from_slug), None)
    to_loc = next((l for l in locations if l["slug"] == to_slug), None)

    if not from_loc or not to_loc:
        flash("Invalid location selection.", "danger")
        return redirect(url_for("admin_new_route"))

    # Floor validation
    if from_loc.get("floor") != to_loc.get("floor"):
        if kind not in ["stairs", "elevator"]:
            flash(f"Locations on different floors ({from_loc.get('floor')} and {to_loc.get('floor')}) must be connected via stairs or elevator.", "danger")
            return redirect(url_for("admin_new_route"))

    # Duplicate check
    for edge in edges:
        if (edge["from"] == from_slug and edge["to"] == to_slug) or \
           (edge["from"] == to_slug and edge["to"] == from_slug):
            flash("This connection already exists.", "danger")
            return redirect(url_for("admin_new_route"))

    edges.append({
        "from": from_slug, "to": to_slug,
        "distance": distance, "type": kind,
        "is_accessible": accessible
    })
    update_data(DATA_PATH, locations, edges)
    flash("Route connection added.", "success")
    return redirect(url_for("admin_routes"))


@app.get("/admin/settings")
@admin_required
def admin_settings():
    locations = get_locations(DATA_PATH)
    edges = get_edges(DATA_PATH)
    return render_template(
        "admin_dashboard.html",
        locations=locations,
        edges=edges,
        admin_tab="settings",
        admin_username=ADMIN_USERNAME,
        active_page="admin",
    )


@app.post("/admin/settings/save")
@admin_required
def admin_settings_save():
    global ADMIN_USERNAME, ADMIN_PASSWORD
    new_user = request.form.get("admin_username")
    new_pass = request.form.get("new_password")
    if new_user:
        ADMIN_USERNAME = new_user
    if new_pass:
        ADMIN_PASSWORD = new_pass
    flash("Settings saved successfully.", "success")
    return redirect(url_for("admin_settings"))


@app.get("/admin/qr/generate-all")
@admin_required
def admin_generate_all_qrs():
    """Utility to generate QR codes for all existing locations."""
    locations = get_locations(DATA_PATH)
    count = 0
    errors = 0
    for loc in locations:
        try:
            generate_qr(loc["slug"])
            count += 1
        except:
            errors += 1
    
    if errors:
        flash(f"Generated {count} QR codes. {errors} failed.", "warning")
    else:
        flash(f"Successfully generated QR codes for all {count} locations.", "success")
    return redirect(url_for("admin_dashboard"))


@app.get("/admin/qr/download/<slug>")
@admin_required
def admin_download_qr(slug: str):
    """Download a QR code as an attachment."""
    qr_dir = BASE_DIR / "static" / "qrcodes"
    filename = f"{slug}.png"
    if not (qr_dir / filename).exists():
        try:
            generate_qr(slug)
        except Exception as e:
            abort(500, f"Could not generate QR: {str(e)}")
            
    return send_from_directory(qr_dir, filename, as_attachment=True)


# ═══════════════════════════════════════ OPERATIONS ROUTES ═══════════════════

@app.get("/ops")
@app.get("/ops/overview")
@admin_required
def operations_dashboard():
    return render_template(
        "operations_dashboard.html",
        **build_operations_dashboard_context(),
    )

@app.get("/ops/assets")
@admin_required
def assets_dashboard():
    return render_template(
        "assets_dashboard.html",
        console_title="Asset Tracking",
        console_subtitle="Real-time equipment monitoring",
        active_console="assets",
        metrics=ASSET_METRICS,
        donut_segments=ASSET_STATUS_SEGMENTS,
        inventory=ASSET_INVENTORY,
        alerts=SECURITY_ALERTS,
    )


@app.get("/ops/safety")
@admin_required
def safety_dashboard():
    return render_template(
        "safety_dashboard.html",
        console_title="Safety & Analytics",
        console_subtitle="Campus security and crowd monitoring",
        active_console="safety",
        protocols=SAFETY_PROTOCOLS,
        events=SAFETY_EVENTS,
        triggers=PANIC_TRIGGERS,
        zones=SAFETY_HEAT_ZONES,
    )


@app.get("/ops/hardware")
@admin_required
def hardware_dashboard():
    return render_template(
        "hardware.html",
        console_title="Hardware Configuration",
        console_subtitle="Beacon and signal management",
        active_console="hardware",
        beacons=BEACON_INVENTORY,
        firmware_status=FIRMWARE_STATUS,
    )


@app.get("/ops/directory")
@admin_required
def directory():
    active_section = request.args.get("section", "all")
    search_query = request.args.get("q", "")
    
    # Simple mock filtering
    entries = DIRECTORY_ENTRIES
    if active_section != "all":
        entries = [e for e in entries if e.get("section_id") == active_section]
    if search_query:
        entries = [e for e in entries if search_query.lower() in e["name"].lower()]

    return render_template(
        "directory.html",
        console_title="Campus Directory",
        console_subtitle="Searchable campus spaces",
        active_console="directory",
        directory_sections=DIRECTORY_SECTIONS,
        active_section=active_section,
        search_query=search_query,
        entries=entries,
    )


# ═══════════════════════════════════════ API ════════════════════════════════

@app.get("/api/locations")
def api_locations():
    return jsonify(get_locations(DATA_PATH))


@app.get("/api/route")
def api_route():
    source_slug = request.args.get("source", "").strip().lower()
    destination_slug = request.args.get("destination", "").strip().lower()
    source = get_location_by_slug(DATA_PATH, source_slug)
    destination = get_location_by_slug(DATA_PATH, destination_slug)
    if source is None or destination is None:
        return jsonify({"error": "Invalid source or destination"}), 400

    filters = {
        "use_elevators": request.args.get("use_elevators") == "on",
        "avoid_stairs": request.args.get("avoid_stairs") == "on",
        "accessible_only": request.args.get("accessible_only") == "on",
    }

    graph = get_graph(DATA_PATH)
    path, total_distance = dijkstra_shortest_path(graph, source_slug, destination_slug, filters)
    route_details = build_route_details(path, graph)
    return jsonify({
        "source": source,
        "destination": destination,
        "path": path,
        "distance": total_distance,
        "steps": route_details,
    })


if __name__ == "__main__":
    app.run(debug=True)
