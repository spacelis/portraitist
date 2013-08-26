/* global dc */
/* global d3 */
/* global crossfilter */

var profileviewer_ns = (function(){
  var fact; // crossfilter object holding data
  var map;
  var map_markers;

  var update_map = function (poi_groups){
    var markers = {};
    for(var i in poi_groups) {
      var poi = poi_groups[i];
      markers[poi.id] = {
        position: [poi.lat, poi.lng],
        info_window: {
          content: poi.name + '<br>' + poi.cate,
          showOn: 'mouseover',
          hideOn: 'mouseout'
        }
      };
    }
    data.markers = markers;
    $('#map-canvas').initMap(data);
  };

  var init_map = function (pois){
    var map_opts = {center: google.maps.LatLng(41, -100),
                    zoom: 3,
                    mapTypeId: google.maps.MapTypeId.ROADMAP};
    map = new google.maps.Map(document.getElementById('map-canvas'), map_opts);
    update_map();
  };

  var time_parser = d3.time.format("%Y-%m-%dT%H:%M:%S").parse;

  var render_charts = function (){
    fact = crossfilter(data);

    var by_week = fact.dimension(function(c){
      //return year_month(c.created_at);
      return d3.time.week(c.created_at);
    });
    var by_category = fact.dimension(function(c){
      return c.place.zcate;
    });
    var by_poi = fact.dimension(function(c){
      //return c.place.id + "\t" + c.place.name;
      c.place.valueOf = function(){
        return c.place.id;
      };
      return c.place;
    });


    var checkins_by_week = by_week.group().reduceCount();
    var checkins_by_category = by_category.group().reduceCount();
    var checkins_by_poi = by_poi.group().reduceCount();



    dc.pieChart('#chart-cate-pie')
      .width(200) // (optional) define chart width, :default = 200
      .height(200) // (optional) define chart height, :default = 200
      .transitionDuration(500) // (optional) define chart transition duration, :default = 350
      .colors(d3.scale.category20())
      .radius(90) // define pie radius
      .innerRadius(40)
      .dimension(by_category) // set dimension
      .group(checkins_by_category) // set group
      .renderTitle(true);

    dc.pieChart('#chart-poi-pie')
      .width(200) // (optional) define chart width, :default = 200
      .height(200) // (optional) define chart height, :default = 200
      .transitionDuration(500) // (optional) define chart transition duration, :default = 350
      .colors(d3.scale.category20())
      .radius(90) // define pie radius
      .innerRadius(40)
      .dimension(by_poi) // set dimension
      .group(checkins_by_poi) // set group
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
      .renderTitle(true);

    dc.barChart("#chart-timeline")
      .width(700) // (optional) define chart width, :default = 200
      .height(200) // (optional) define chart height, :default = 200
      .transitionDuration(500) // (optional) define chart transition duration, :default = 500
      .dimension(by_week) // set dimension
      .group(checkins_by_week) // set group
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
  };

  var init_charts = function (screen_name) {
    d3.json(
      '/api/expert_checkins?screen_name=' + screen_name,
      function(err, json){
        if (err){
          alert("Fail to get data for " + screen_name);
        }
        else{
          data = json;
          data.forEach(function (c){
            c.created_at = time_parser(c.created_at);
          });
          render_charts();
        }
      }
    );
  };

  return {
    initMap: init_map,
    initCharts: init_charts,
  };
})();
