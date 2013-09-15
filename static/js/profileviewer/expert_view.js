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

  var REGIONS = {
      'Chicago': {lat: [41.4986, 42.0232],
                  lng: [-88.1586, -87.3573]},
      'New York': {lat: [40.4110, 40.9429],
                   lng: [-74.2918, -73.7097]},
      'Los Angeles': {lat: [33.7463, 34.2302],
                      lng: [-118.6368, -117.9053]},
      'San Francisco': {lat: [37.7025, 37.8045],
                        lng: [-122.5349, -122.3546]}};
  function update_map (poi_groups){
    var pois = poi_groups.top(30);
    map.removeMarkers();
    for(var i in pois) {
      if(pois[i].value === 0) {continue;}
      var poi = pois[i].key;
      map.addMarker({
        lat: poi.lat,
        lng: poi.lng,
        title: poi.name + ' (' + pois[i].value + ' check-ins)\n' + poi.category + ', ' + poi.zcategory,
        infoWindow: {
          content: poi.name + ' (' + pois[i].value + ' check-ins)<br>' + poi.category + ', ' + poi.zcategory,
        },
        icon: '/static/images/profileviewer/map_icons/' + poi.cate_id + '_black.png',
      });
    }
    map.fitZoom();
    if(map.getZoom() > 17){
      map.setZoom(17);
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
  var zcate_chart, cate_chart, poi_chart, region_chart, timeline_chart;
  var allpois;

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
      return c.place.zcategory;
    });
    var by_poi = fact.dimension(function(c){
      //return c.place.id + "\t" + c.place.name;
      c.place.valueOf = function(){
        return c.place.id;
      };
      return c.place;
    });
    var by_region = fact.dimension(function(c){
      for(var r in REGIONS){
        if ((REGIONS[r].lat[0] < c.place.lat && c.place.lat < REGIONS[r].lat[1] &&
             REGIONS[r].lng[0] < c.place.lng && c.place.lng < REGIONS[r].lng[1] )){
          return r;
        }
      }
      return 'Other';
    });

    var checkins_by_week = by_week.group().reduceCount();
    var checkins_by_category = by_category.group().reduceCount();
    var checkins_by_zcate = by_zcate.group().reduceCount();
    var checkins_by_poi = by_poi.group().reduceCount();
    var checkins_by_region = by_region.group().reduceCount();
    allpois = checkins_by_poi.all();

    var w = $("#chart-zcate-pie").width();
    zcate_chart = dc.pieChart("#chart-zcate-pie")
      .width(w) // (optional) define chart width, :default = 200
      .height(w) // (optional) define chart height, :default = 200
      .transitionDuration(500) // (optional) define chart transition duration, :default = 350
      .colors(d3.scale.category20())
      .radius(w / 200 * 90) // define pie radius
      .innerRadius(w / 200 * 40)
      .dimension(by_zcate) // set dimension
      .group(checkins_by_zcate) // set group
      .on("filtered", function(chart, filter){
        update_map(checkins_by_poi);
      })
      .title(function (obj){
        return obj.data.key + ":  " + obj.data.value + " check-in(s)";
      })
      .renderTitle(true);

    w = $("#chart-cate-pie").width();
    cate_chart = dc.pieChart("#chart-cate-pie")
      .width(w) // (optional) define chart width, :default = 200
      .height(w) // (optional) define chart height, :default = 200
      .transitionDuration(500) // (optional) define chart transition duration, :default = 350
      .colors(d3.scale.category20())
      .radius(w / 200 * 90) // define pie radius
      .innerRadius(w / 200 * 40)
      .dimension(by_category) // set dimension
      .group(checkins_by_category) // set group
      .slicesCap(10)
      .on("filtered", function(chart, filter){
        update_map(checkins_by_poi);
      })
      .title(function (obj){
        return obj.data.key + ":  " + obj.data.value + " check-in(s)";
      })
      .renderTitle(true);

    w = $("#chart-region-pie").width();
    region_chart = dc.pieChart("#chart-region-pie")
      .width(w) // (optional) define chart width, :default = 200
      .height(w) // (optional) define chart height, :default = 200
      .transitionDuration(500) // (optional) define chart transition duration, :default = 350
      .colors(d3.scale.category20())
      .radius(w / 200 * 90) // define pie radius
      .innerRadius(w / 200 * 40)
      .dimension(by_region) // set dimension
      .group(checkins_by_region) // set group
      .slicesCap(10)
      .on("filtered", function(chart, filter){
        update_map(checkins_by_poi);
      })
      .title(function (obj){
        return obj.data.key + ":  " + obj.data.value + " check-in(s)";
      })
      .renderTitle(true);

    w = $("#chart-poi-pie").width();
    poi_chart = dc.pieChart("#chart-poi-pie")
      .width(w) // (optional) define chart width, :default = 200
      .height(w) // (optional) define chart height, :default = 200
      .transitionDuration(500) // (optional) define chart transition duration, :default = 350
      .colors(d3.scale.category20())
      .radius(w / 200 * 90) // define pie radius
      .innerRadius(w / 200 * 40)
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
          return x + ":  " + obj.data.value + " check-in(s)";
        }
        else{
          return obj.data.key + ":  " + obj.data.value + " check-in(s)";
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
      .renderTitle(true);

    w = $("#chart-timeline").width();
    timeline_chart = dc.barChart("#chart-timeline")
      .width(w) // (optional) define chart width, :default = 200
      .height(120) // (optional) define chart height, :default = 200
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

  function initCharts (hash_id) {
    d3.json(
      '/api/expert_checkins?hash_id=' + hash_id,
      function(err, json){
        if (err){
          alert("Fail to get data for " + hash_id);
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

  function focusTopic(topic, chart){
    if(chart === 'p'){
      var p;
      for(var i in allpois){
        if(topic === allpois[i].key.valueOf()){
          p = allpois[i].key;
          break;
        }
      }
      poi_chart.filter(p);
    }
    else if(chart === 'c'){
      cate_chart.filter(topic);
    }
    else if(chart === 'z'){
      zcate_chart.filter(topic);
    }
    else if(chart === 'r'){
      region_chart.filter(topic);
    }
    dc.redrawAll();
  }

  function getChart(name){
    return poi_chart;
  }

  return {
    initCharts: initCharts,
    focusTopic: focusTopic,
    getChart: getChart
  };
})();
