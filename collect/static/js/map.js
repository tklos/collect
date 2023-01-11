
function calculate_map_bounds(points) {
    var bounds = new google.maps.LatLngBounds();
    for (var i = 0; i < points.length; i++)
        bounds.extend(points[i]);

    return bounds;
}


/* Taken from https://stackoverflow.com/a/13274361 */
function calculate_map_zoom(bounds, map_height, map_width) {
    var WORLD_DIM = {height: 256, width: 256};
    var ZOOM_MAX = 21;

    function latRad(lat) {
        var sin = Math.sin(lat * Math.PI / 180);
        var radX2 = Math.log((1 + sin) / (1 - sin)) / 2;
        return Math.max(Math.min(radX2, Math.PI), -Math.PI) / 2;
    }

    function zoom(mapPx, worldPx, fraction) {
        return Math.floor(Math.log(mapPx / worldPx / fraction) / Math.LN2);
    }

    var ne = bounds.getNorthEast();
    var sw = bounds.getSouthWest();

    var latFraction = (latRad(ne.lat()) - latRad(sw.lat())) / Math.PI;

    var lngDiff = ne.lng() - sw.lng();
    var lngFraction = ((lngDiff < 0) ? (lngDiff + 360) : lngDiff) / 360;

    var latZoom = zoom(map_height, WORLD_DIM.height, latFraction);
    var lngZoom = zoom(map_width, WORLD_DIM.width, lngFraction);

    return Math.max(Math.min(latZoom, lngZoom, ZOOM_MAX), 0);
}


function initMap() {
    /* Locations */
    var locations = JSON.parse(document.getElementById("id-locations-l").textContent);

    /* Points */
    var points = [];
    for (var i = 0; i < locations.length; i++)
        points.push({
            lat: locations[i][1],
            lng: locations[i][2],
        });

    /* Map */
    var map_div = document.getElementById("map");
    var map_bounds = points.length > 0 ? calculate_map_bounds(points) : null;
    map = new google.maps.Map(map_div, {
        center: map_bounds ? map_bounds.getCenter() : new google.maps.LatLng(0, 0),
        zoom: map_bounds ? calculate_map_zoom(map_bounds, map_div.clientHeight, map_div.clientWidth) : 0,
    });

    /* Path */
    var path = new google.maps.Polyline({
        path: points,
        strokeColor: "#000000",
        strokeOpacity: 1.0,
        strokeWeight: 1,
        map: map,
    });

    /* Markers */
    var markers = [];
    for (var i = 0; i < locations.length; i++)
        markers.push(
            new google.maps.Marker({
                position: points[i],
                info_window_content: "#" + locations[i][0] + ": " + locations[i][3],
                map: null,
            })
        );
    if (markers.length >= 2) {
        markers[0].setLabel("S");
        markers[markers.length-1].setLabel("E");
        markers[0].setMap(map);
        markers[markers.length-1].setMap(map);
    }

    /* Info window */
    var info_window = new google.maps.InfoWindow();
    for (var i = 0; i < locations.length; i++) {
        markers[i].addListener("click", function() {
            info_window.setContent(this.info_window_content);
            info_window.open(map, this);
        });
    }

    /* Show markers panel */
    var map_panel = document.createElement("div");
    map_panel.style.backgroundColor = "#fff";
    map_panel.style.borderRadius = "3px";
    map_panel.style.height = "39px";
    map_panel.style.display = "table-cell";
    map_panel.style.marginTop = "10px";
    map_panel.style.boxShadow = "rgba(0, 0, 0, 0.3) 0px 1px 4px -1px";
    map_panel.style.cursor = "pointer";
    map_panel.style.zIndex = "1";

    var map_panel_inner = document.createElement("div");
    map_panel_inner.style.color = "rgb(86, 86, 86)";
    map_panel_inner.style.fontFamily = "Roboto,Arial,sans-serif";
    map_panel_inner.style.fontSize = "15px";
    map_panel_inner.style.fontWeight = "400";
    map_panel_inner.style.paddingLeft = "12px";
    map_panel_inner.style.paddingRight = "12px";
    map_panel_inner.style.textAlign = "center";
    map_panel_inner.style.lineHeight = "39px";
    map_panel_inner.innerHTML = '<input type="checkbox" id="map-checkbox"> Show markers';
    map_panel_inner.addEventListener("click", function(event) {
        var checkbox = document.getElementById("map-checkbox");
        if (event.target != checkbox)
            checkbox.checked = !checkbox.checked;

        var new_map = checkbox.checked ? map : null;
        for (var i = 1; i < markers.length-1; i++)
            markers[i].setMap(new_map);
        info_window.close();
    });

    map_panel.appendChild(map_panel_inner);

    map.controls[google.maps.ControlPosition.TOP_CENTER].push(map_panel);
}

