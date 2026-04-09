function initCampusMap(element) {
  const locations = JSON.parse(element.dataset.locations || "[]");
  const path = JSON.parse(element.dataset.path || "[]");
  const locationBySlug = new Map(locations.map((location) => [location.slug, location]));

  const map = L.map(element, {
    crs: L.CRS.Simple,
    minZoom: -1,
    maxZoom: 2,
    zoomControl: true,
  });

  const bounds = [[0, 0], [80, 100]];
  L.rectangle(bounds, {
    color: "#c9baa1",
    weight: 1,
    fillColor: "#f7f0e4",
    fillOpacity: 0.95,
  }).addTo(map);
  map.fitBounds(bounds, { padding: [10, 10] });

  const landmarkLayer = L.layerGroup().addTo(map);
  locations.forEach((location) => {
    const marker = L.circleMarker([location.y, location.x], {
      radius: 7,
      color: "#084c39",
      fillColor: "#0b6e4f",
      fillOpacity: 0.9,
      weight: 2,
    });
    marker.bindPopup(`<strong>${location.name}</strong><br>${location.description}`);
    marker.addTo(landmarkLayer);
  });

  if (path.length > 1) {
    const routePoints = path
      .map((slug) => locationBySlug.get(slug))
      .filter(Boolean)
      .map((location) => [location.y, location.x]);

    L.polyline(routePoints, {
      color: "#e07a16",
      weight: 5,
      opacity: 0.92,
      lineJoin: "round",
    }).addTo(map);

    routePoints.forEach((point, index) => {
      L.circleMarker(point, {
        radius: index === 0 || index === routePoints.length - 1 ? 9 : 6,
        color: "#9a4700",
        fillColor: index === routePoints.length - 1 ? "#ffb703" : "#f48c06",
        fillOpacity: 1,
        weight: 2,
      }).addTo(map);
    });
  }
}

document.querySelectorAll("[data-map]").forEach(initCampusMap);
