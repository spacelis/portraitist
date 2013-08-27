/* global dc */
/* global d3 */
/* global crossfilter */

var TopicView = (function(){
  function fmtInfoW (place) {
    return 'Name: <b>' + place.name + '</b><br>Category: <b>' + place.category + '</b>';
  }

  function MapMarker(map, place){
    this.marker = new google.maps.Marker({
      position: new google.maps.LatLng(place.lat, place.lng),
      map: this.map,
    });
    this.infowindow = new google.maps.InfoWindow({
      content: fmtInfoW(place),
    });
    google.maps.event.addListener(this.marker, 'mouseover', function (){
      this.infowindow.open(map, this.marker);
    });
    google.maps.event.addListener(this.marker, 'mouseout', function (){
      this.infowindow.close();
    });
  }

  function View(expert) {  // expert ={screen_name, checkins}

    // ------------------ Prepare Data ---------------------
    var time_parser = d3.time.format("%Y-%m-%dT%H:%M:%S").parse;
    expert.checkins.forEach(function (c){
      c.created_at = time_parser(c.created_at);
    });
    this.fact = crossfilter(expert.checkins);
    this.week_dim = this.fact.dimension(function(c){
      return d3.time.week(c.created_at);
    });
    this.category_dim = this.fact.dimension(function(c){
      return c.place.zcate;
    });
    this.poi_dim = this.fact.dimension(function(c){
      c.place.valueOf = function(){
        return c.place.id;
      };
      return c.place;
    });

    this.checkins_by_week = this.week_dim.group().reduceCount();
    this.checkins_by_category = this.category_dim.group().reduceCount();
    this.checkins_by_poi = this.poi_dim.group().reduceCount();

    // ---------------- Prepare Map ----------------------
    //var map_opts = {center: google.maps.LatLng(41, -100),
                    //zoom: 3,
                    //mapTypeId: google.maps.MapTypeId.ROADMAP};
    //this.map = new google.maps.Map(document.getElementById('map-canvas-' + expert.screen_name), map_opts);
    //this.map_markers = [];

    //this.update_map = function(){
      //var i;
      //var places = this.category_dim.top(30);
      //if (this.map_markers.length === 0){
        //for(i in places){
          //this.map_markers.push(new MapMarker(this.map, places[i]));
        //}
      //}
      //else{
        //for(i in places){
          //var p = places[i];
          //this.map_markers[i].marker.setPosition(google.maps.LatLng(p.lat, p.lng));
          //this.map_markers[i].infowindow.setContent(fmtInfoW(p));
        //}
      //}
    //};

    // --------------------- Prepare Charts ---------------------
    dc.pieChart('#chart-cate-pie-' + expert.screen_name)
      .width(200) // (optional) define chart width, :default = 200
      .height(200) // (optional) define chart height, :default = 200
      .transitionDuration(500) // (optional) define chart transition duration, :default = 350
      .colors(d3.scale.category20())
      .radius(90) // define pie radius
      .innerRadius(40)
      .dimension(this.category_dim) // set dimension
      .group(this.checkins_by_category) // set group
      .renderTitle(true);

    dc.pieChart('#chart-poi-pie-' + expert.screen_name)
      .width(200) // (optional) define chart width, :default = 200
      .height(200) // (optional) define chart height, :default = 200
      .transitionDuration(500) // (optional) define chart transition duration, :default = 350
      .colors(d3.scale.category20())
      .radius(90) // define pie radius
      .innerRadius(40)
      .dimension(this.poi_dim) // set dimension
      .group(this.checkins_by_poi) // set group
      .label(function (obj){
        var x = obj.data.key.name;
        if(x){
          return x;
        }
        else{
          return obj.data.key;
        }
      })
      .slicesCap(10)
      .title(function(d) {
        return d.data.key.name + ": " + d.value; })
      .renderTitle(true);

    dc.barChart("#chart-timeline-" + expert.screen_name)
      .width(700) // (optional) define chart width, :default = 200
      .height(200) // (optional) define chart height, :default = 200
      .transitionDuration(500) // (optional) define chart transition duration, :default = 500
      .dimension(this.week_dim) // set dimension
      .group(this.checkins_by_week) // set group
      .elasticY(true)
      .elasticX(true)
      .x(d3.time.scale().domain([new Date(2000, 0, 1), new Date(2013, 7, 31)]))
      .round(d3.time.week.round)
      .xUnits(d3.time.weeks)
      .centerBar(true)
      .gap(1)
      .renderHorizontalGridLines(true)
      .renderVerticalGridLines(true)
      .brushOn(true)
      .title(function(d) { return "Value: " + d.value; })
      .renderTitle(true);

    dc.renderAll();
  }

  var views = {};

  function initCharts(names){
    d3.json(
      '/api/expert_checkins?names=' + names.join(),
      function(err, data){
        if (err){
          alert("Fail to get data for " + names.joins());
        }
        else{
          for(var i in data){
            views[i] = new View(data[i]);
          }
        }
      }
    );
  }

  return {
    initCharts: initCharts,
    views: views,
  };
})();
