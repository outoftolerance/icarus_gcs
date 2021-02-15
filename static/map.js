var icarus_map;
var icarus_marker_layergroup;
var icarus_trail_layergroup;

const icon_balloon = L.icon({
    iconUrl: '../assets/8_bit_balloon_pin.png',
    iconSize:     [32, 32],
    iconAnchor:   [16, 16],
    popupAnchor:  [0, -16]
});

const marker_options = {
    icon: icon_balloon,
};

const popup_options = {
    closeOnClick: false,
    autoClose: false,
    autoPan: false,
};

const trail_options = {
    color: 'red', 
    weight: 1,
    opacity: 0.75,
};

var channel;
var config;

new QWebChannel(qt.webChannelTransport, function (input_channel) {
    channel = input_channel.objects.python_link;

    channel.get_config(function(input_config) {
        config = JSON.parse(input_config);

        icarus_map = L.map('iris_map_div').setView([config.home_latitude, config.home_longitude], config.home_zoom);

        /* Available Map Styles:
         - mapbox/streets-v11
         - mapbox/outdoors-v11
         - mapbox/light-v10
         - mapbox/dark-v10
         - mapbox/satellite-v9
         - mapbox/satellite-streets-v11
         */

        L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}', {
            attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
            maxZoom: config.max_zoom,
            minZoom: config.min_zoom,
            id: 'mapbox/outdoors-v11',
            tileSize: 512,
            zoomOffset: -1,
            accessToken: ''
        }).addTo(icarus_map);

        icarus_marker_layergroup = L.layerGroup().addTo(icarus_map);
        icarus_trail_layergroup = L.layerGroup().addTo(icarus_map);
    });
});

/*
 * Updates device markers and popups
 */
function mapCenterUpdate(location) {
    icarus_map.setView([location.latitude, location.longitude])
}

/*
 * Updates device markers and popups
 */
function icarusDeviceUpdate(devices) {
    //Grab all existing markers so we can update them
    existing_markers = icarus_marker_layergroup.getLayers();
    updated_markers = [];

    //For each device, update the marker, or create a new one
    for (var device in devices) {
        marker_found = false;

        for (var j = 0; j < existing_markers.length; j++) {
            if (existing_markers[j].getPopup().getContent() == devices[device].id) {
                existing_markers[j].setLatLng([devices[device].latitude, devices[device].longitude]);
                existing_markers[j].getPopup().setContent(devices[device].id);

                //Add this to the updated markers list
                updated_markers.push(existing_markers[i]);

                //Marker was found!
                marker_found = true;
            }
        }

        //If the marker was not found, we need to create a new one
        if (!marker_found) {
            new_icarus_marker = L.marker([devices[device].latitude, devices[device].longitude], marker_options).addTo(icarus_marker_layergroup);
            new_icarus_marker.bindPopUp(devices[device].id, popup_options);
        }
    }

    //All non-updated markers need to be removed
    for (var i = 0; i < existing_markers.length; i++) {
        //If it's existing and not updated, it means it shouldn't exist any more
        if (!updated_markers.includes(existing_markers[i])) {
            //Remove from the layergroup
            icarus_marker_layergroup.removeLayer(existing_markers[i]);
        }
    }
}

/*
 * Updates device trail polylines
 */
function icarusTrailUpdate(trails) {
    //It's not possible to identify polylines so we just have to clear them all first
    icarus_trail_layergroup.clearLayers();

    //Now we add all trails again
    for (var trail in trails) {
        L.polyline(trails[trail].points, trail_options).addTo(icarus_trail_layergroup);
    }
}

/*
 * Places a marker where an event has occurred
 */
function icarusEventMarkerAdd(event) {

}