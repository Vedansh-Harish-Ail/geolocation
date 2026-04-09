const campusBlocks = [];

function mapTheme(mode) {
  switch (mode) {
    case "asset":
      return {
        ground: "#101b2f",
        border: "#314665",
        fill: "#1f304d",
        building: "#293b57",
        path: "#2f4866",
        marker: "#2d8cff",
        route: "#ff8b3d",
      };
    case "safety":
      return {
        ground: "#111a28",
        border: "#42536b",
        fill: "#213247",
        building: "#3f4f61",
        path: "#37506b",
        marker: "#ff5b61",
        route: "#ff5b61",
      };
    case "hardware":
      return {
        ground: "#eef3fb",
        border: "#c5d3e8",
        fill: "#f8fbff",
        building: "#dfe8f4",
        path: "#b0c1db",
        marker: "#2f69c5",
        route: "#2f69c5",
      };
    default:
      return {
        ground: "#f3f7fd",
        border: "#d3deef",
        fill: "#fbfdff",
        building: "#e4edf8",
        path: "#bfd1eb",
        marker: "#2f69c5",
        route: "#2f69c5",
      };
  }
}

function drawCampusScene(map, theme) {
  const bounds = [[0, 0], [84, 100]];
  L.rectangle(bounds, {
    color: theme.border,
    weight: 1,
    fillColor: theme.ground,
    fillOpacity: 0.96,
  }).addTo(map);

  // Hardcoded paths and blocks removed for clean slate

  map.fitBounds(bounds, { padding: [10, 10] });
}

function buildTooltip(label, subtitle = "") {
  return `<div class="map-tooltip"><strong>${label}</strong>${subtitle ? `<br>${subtitle}` : ""}</div>`;
}

function addPlannerContent(map, element, theme) {
  const locations = JSON.parse(element.dataset.locations || "[]");
  const edges = JSON.parse(element.dataset.edges || "[]");
  const path = JSON.parse(element.dataset.path || "[]");
  const locationBySlug = new Map(locations.map((location) => [location.slug, location]));

  edges.forEach((edge) => {
    const start = locationBySlug.get(edge.from);
    const end = locationBySlug.get(edge.to);
    if (!start || !end) {
      return;
    }
    L.polyline(
      [
        [start.y, start.x],
        [end.y, end.x],
      ],
      {
        color: "#afc5e4",
        weight: 4,
        opacity: 0.68,
        dashArray: "6 10",
      },
    ).addTo(map);
  });

  locations.forEach((location) => {
    const marker = L.circleMarker([location.y, location.x], {
      radius: 7,
      color: "#ffffff",
      weight: 2,
      fillColor: theme.marker,
      fillOpacity: 1,
    }).addTo(map);
    marker.bindTooltip(buildTooltip(location.name, location.description), {
      direction: "top",
      opacity: 1,
      className: "",
    });
  });

  if (path.length > 1) {
    const points = path
      .map((slug) => locationBySlug.get(slug))
      .filter(Boolean)
      .map((location) => [location.y, location.x]);

    L.polyline(points, {
      color: theme.route,
      weight: 6,
      opacity: 1,
      lineCap: "round",
    }).addTo(map);

    points.forEach((point, index) => {
      L.circleMarker(point, {
        radius: index === points.length - 1 ? 10 : 8,
        color: "#ffffff",
        weight: 3,
        fillColor: index === 0 ? "#d39b3d" : "#2f69c5",
        fillOpacity: 1,
      }).addTo(map);
    });
  }
}

function statusColor(status) {
  const tone = (status || "").toLowerCase();
  if (tone.includes("maintenance") || tone.includes("offline")) {
    return "#ff5b61";
  }
  if (tone.includes("transit") || tone.includes("battery")) {
    return "#ff9f43";
  }
  return "#2d8cff";
}

function addAssetContent(map, markers) {
  markers.forEach((item) => {
    const marker = L.circleMarker([item.y, item.x], {
      radius: 10,
      color: "#ffffff",
      weight: 2,
      fillColor: statusColor(item.status),
      fillOpacity: 0.95,
    }).addTo(map);
    marker.bindTooltip(buildTooltip(item.name, item.last_seen || item.location), {
      direction: "top",
      opacity: 1,
    });

    L.circle([item.y, item.x], {
      radius: 4,
      color: statusColor(item.status),
      weight: 1,
      fillColor: statusColor(item.status),
      fillOpacity: 0.14,
    }).addTo(map);
  });
}

function addSafetyContent(map, zones) {
  zones.forEach((zone) => {
    const color = zone.intensity > 0.8 ? "#ff4f5e" : zone.intensity > 0.6 ? "#ff9f43" : "#5ac1ff";
    L.circle([zone.y, zone.x], {
      radius: zone.radius,
      color,
      weight: 1,
      fillColor: color,
      fillOpacity: 0.28,
    }).addTo(map).bindTooltip(buildTooltip(zone.label), {
      direction: "top",
      opacity: 1,
    });
  });
}

function initMap(element) {
  const mode = element.dataset.mode || "planner";
  const theme = mapTheme(mode);
  const map = L.map(element, {
    crs: L.CRS.Simple,
    minZoom: -1,
    maxZoom: 2,
    zoomControl: true,
    attributionControl: false,
  });

  drawCampusScene(map, theme);

  if (mode === "planner") {
    addPlannerContent(map, element, theme);
    return;
  }

  if (mode === "safety") {
    const zones = JSON.parse(element.dataset.heat || "[]");
    addSafetyContent(map, zones);
    return;
  }

  const markers = JSON.parse(element.dataset.markers || "[]");
  addAssetContent(map, markers);
}

function initDonut(chart) {
  const segments = JSON.parse(chart.dataset.donut || "[]");
  let progress = 0;
  const stops = segments
    .map((segment) => {
      const start = progress;
      progress += segment.value;
      return `${segment.color} ${start}% ${progress}%`;
    })
    .join(", ");

  chart.style.background = `conic-gradient(${stops})`;
}

document.querySelectorAll("[data-map]").forEach(initMap);
document.querySelectorAll("[data-donut]").forEach(initDonut);
