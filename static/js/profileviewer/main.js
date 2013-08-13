function init(){
  $('#map-canvas').initMap({
    // Set the center of the map to Paris
    center: [ 48.861553 , 2.351074 ],
    markers : {
      paris_marker: { position: 'Paris, France' },
      london : { position: 'London, UK' }
    }
  });
}
