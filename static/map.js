var icarus_map;
var marker_layergroup;
var trail_layergroup;

var icon_balloon = L.icon({
    iconUrl: '../assets/8_bit_balloon_pin.png',
    iconSize:     [32, 32],
    iconAnchor:   [16, 16],
    popupAnchor:  [0, -16]
});

var marker_options = {
    icon: icon_balloon,
}

var popup_options = {
    closeOnClick: false,
    autoClose: false,
    autoPan: false,
}

var trail_options = {
    color: 'red', 
    weight: 1,
    opacity: 0.75,
}

var python_link;
var python_config;

new QWebChannel(qt.webChannelTransport, function (channel) {
    python_link = channel.objects.python_link;

    python_link.get_config(function(config) {
        python_config = config;

        icarus_map = L.map('iris_map_div').setView([python_config[0], python_config[1]], 12);

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
            maxZoom: 18,
            id: 'mapbox/outdoors-v11',
            tileSize: 512,
            zoomOffset: -1,
            accessToken: ''
        }).addTo(icarus_map);

        marker_layergroup = L.layerGroup().addTo(icarus_map);
        trail_layergroup = L.layerGroup().addTo(icarus_map);
    });
});

function update_map()
{
    
}

var timer = setInterval(update_map, 250);