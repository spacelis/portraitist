/* global dc */
/* global d3 */
/* global crossfilter */
/* global GMaps */

var profileviewer_ns = (function(){
  var fact; // crossfilter object holding data
  var map;
  //var map_infowindow = new google.maps.InfoWindow({
    //maxWidth: 300
  //});
  var data;

  function update_map (poi_groups){
    var pois = poi_groups.top(30);
    map.removeMarkers();
    for(var i in pois) {
      if(pois[i].value === 0) {continue;}
      var poi = pois[i].key;
      map.addMarker({
        lat: poi.lat,
        lng: poi.lng,
        title: '[' + poi.id + '] ' + poi.name,
        infoWindow: {
          content: poi.name + '<br>' + poi.category + ', ' + poi.zcate,
        }
      });
    }
    map.fitZoom();
    if(map.getZoom() > 19){
      map.setZoom(19);
    }
  }

  function renderMap (poi_groups){
    map = new GMaps({
      lat: 41.0,
      lng: -100.0,
      div: 'map-canvas',
      zoom: 3,
    });
    update_map(poi_groups);
  }

  var time_parser = d3.time.format("%Y-%m-%dT%H:%M:%S").parse;
  var zcate_chart, cate_chart, poi_chart, timeline_chart;

  function render_charts (){
    fact = crossfilter(data);

    var by_week = fact.dimension(function(c){
      //return year_month(c.created_at);
      return d3.time.week(c.created_at);
    });
    var by_category = fact.dimension(function(c){
      return c.place.category;
    });
    var by_zcate = fact.dimension(function(c){
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
    var checkins_by_zcate = by_zcate.group().reduceCount();
    var checkins_by_poi = by_poi.group().reduceCount();

    var w = $("#chart-zcate-pie").width();
    zcate_chart = dc.pieChart("#chart-zcate-pie")
      .width(w) // (optional) define chart width, :default = 200
      .height(200) // (optional) define chart height, :default = 200
      .transitionDuration(500) // (optional) define chart transition duration, :default = 350
      .colors(d3.scale.category20())
      .radius(90) // define pie radius
      .innerRadius(40)
      .dimension(by_zcate) // set dimension
      .group(checkins_by_zcate) // set group
      .on("filtered", function(chart, filter){
        update_map(checkins_by_poi);
      })
      .renderTitle(true);

    w = $("#chart-cate-pie").width();
    cate_chart = dc.pieChart("#chart-cate-pie")
      .width(w) // (optional) define chart width, :default = 200
      .height(200) // (optional) define chart height, :default = 200
      .transitionDuration(500) // (optional) define chart transition duration, :default = 350
      .colors(d3.scale.category20())
      .radius(90) // define pie radius
      .innerRadius(40)
      .dimension(by_category) // set dimension
      .group(checkins_by_category) // set group
      .slicesCap(10)
      .on("filtered", function(chart, filter){
        update_map(checkins_by_poi);
      })
      .renderTitle(true);

    w = $("#chart-poi-pie").width();
    poi_chart = dc.pieChart("#chart-poi-pie")
      .width(w) // (optional) define chart width, :default = 200
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
      .title(function (obj){
        var x = obj.data.key.name;
        if(x){
          return x + ": " + obj.data.value;
        }
        else{
          return obj.data.key + ": " + obj.data.value;
        }
      })
      .slicesCap(10)
      .on("filtered", function(chart, filter){
        if (chart.hasFilter(filter)){
          update_map({top: function(x){ return [{key: filter}]; }});
        }
        else{
          update_map(checkins_by_poi);
        }
      })
      .legend(dc.legend().x(300).y(10).itemHeight(13).gap(5))
      .renderTitle(true);

    w = $("#chart-timeline").width();
    timeline_chart = dc.barChart("#chart-timeline")
      .width(w) // (optional) define chart width, :default = 200
      .height(200) // (optional) define chart height, :default = 200
      .transitionDuration(500) // (optional) define chart transition duration, :default = 500
      .dimension(by_week) // set dimension
      .group(checkins_by_week) // set group
      .elasticY(false)
      .elasticX(false)
      .x(d3.time.scale().domain([new Date(2009, 0, 1), new Date(2013, 7, 0)]))
      .round(d3.time.week.round)
      .xUnits(d3.time.weeks)
      .centerBar(true)
      .gap(1)
      .renderHorizontalGridLines(true)
      .renderVerticalGridLines(true)
      .brushOn(true)
      .title(function(d) { return "Value: " + d.value; })
      .on("filtered", function(chart, filter){
        update_map(checkins_by_poi);
      })
      .renderTitle(true);

    dc.renderAll();
    renderMap(checkins_by_poi);
  }

  function initCharts (screen_name) {
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
  }

  function focusPOI(place) {
    place.valueOf = function(){
      return place.id;
    };
    poi_chart.filter(place);
    dc.redrawAll();
  }

  function focusCate(cate){
    cate_chart.filter(cate);
    dc.redrawAll();
  }

  function focusZCate(zcate){
    zcate_chart.filter(zcate);
    dc.redrawAll();
  }

  return {
    initCharts: initCharts,
    focusCate: focusCate,
    focusPOI: focusPOI,
    focusZCate: focusZCate
  };
})();
