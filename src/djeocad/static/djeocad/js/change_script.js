function map_init(map, options) {

    function setLineStyle(feature) {
      if (feature.properties.popupContent.linetype) {
        return {"color": feature.properties.popupContent.color, "weight": 3 };
      } else {
        return {"color": feature.properties.popupContent.color, "weight": 3, dashArray: "10, 10" };
      }
    }

    const base_map = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      {
        maxZoom: 19,
      }).addTo(map);

    const layer_control = L.control.layers(null).addTo(map);
    const marker_layer = L.layerGroup().addTo(map);

    function getCollections() {
      // add layer groups
      collection = JSON.parse(document.getElementById("layer_data").textContent);
      if (collection !== null) {
        for (layer_name of collection) {
          window[layer_name] = L.layerGroup().addTo(map);
          layer_control.addOverlay(window[layer_name], layer_name);
        }
      }
      // add objects to layers
      collection = JSON.parse(document.getElementById("marker_data").textContent);
      for (marker of collection.features) {
        // let author = marker.properties.popupContent.layer
        L.geoJson(marker).addTo(marker_layer);
      }
      // fit bounds
      map.fitBounds(L.geoJson(collection).getBounds(), {padding: [30,30]});
      collection = JSON.parse(document.getElementById("line_data").textContent);
      if (collection !== null) {
        for (line of collection.features) {
          let name = line.properties.popupContent.layer
          L.geoJson(line, {style: setLineStyle}).addTo(window[name]);
        }
      }
    }

    getCollections()

    function onMapClick(e) {
      var inputlat = document.getElementById("id_lat");
        var inputlong = document.getElementById("id_long");
        inputlat.setAttribute('value', e.latlng.lat);
        inputlong.setAttribute('value', e.latlng.lng);
        marker_layer.clearLayers();
        L.marker([e.latlng.lat, e.latlng.lng]).addTo(marker_layer)
    }

    map.on('click', onMapClick);
}
