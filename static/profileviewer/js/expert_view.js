/* eslint-env node, amd */
/* global dc */
/* global jQuery */
/* global d3 */
/* global crossfilter */
/* global GMaps */

(function(){

function _profileviewer(d3, crossfilter, dc, GMaps, $){
  var _fact; // crossfilter object holding data
  var _map;
  //var map_infowindow = new google.maps.InfoWindow({
    //maxWidth: 300
  //});
  var _data;
  var _created_at;

  //var time_parser = d3.time.format.utc("%a %b %d %H:%M:%S +0000 %Y").parse;
  var time_parser = function(d){return new Date(d);};
  var _chartTypeMap;
  var _allpois;
  var _filter_set;

  var _REGIONS = {
      "Chicago": {lat: [41.4986, 42.0232],
                  lng: [-88.1586, -87.3573]},
      "New York": {lat: [40.4110, 40.9429],
                   lng: [-74.2918, -73.7097]},
      "Los Angeles": {lat: [33.7463, 34.2302],
                      lng: [-118.6368, -117.9053]},
      "San Francisco": {lat: [37.7025, 37.8045],
                        lng: [-122.5349, -122.3546]}};

  var _COLORPALETTE = d3.scale.ordinal().range(
    [
      0x1f77b4, 0xff7f0e, 0x2ca02c, 0xd62728, 0x9467bd, 0x8c564b, 0xe377c2, 0xbcbd22, 0x17becf,
      0x2D34CB, 0xffbb78, 0x98df8a, 0xff9896, 0xc5b0d5, 0xc49c94, 0xf7b6d2, 0xdbdb8d, 0x9edae5
    ].map(function(value){return new d3.rgb(value >> 16, value >> 8 & 0xff, value & 0xff) + ""; })
  );

  function _updateMap (poi_groups){
    var pois = poi_groups.top(30);
    _map.removeMarkers();
    for(var i in pois) {
      if(pois[i].value === 0) {continue;}
      var poi = pois[i].key;
      _map.addMarker({
        lat: poi.lat,
        lng: poi.lng,
        title: poi.name + " (" + pois[i].value + " check-ins)\n" + poi.category.name + ", " + poi.category.zero_category_name,
        infoWindow: {
          content: "<b>" + poi.name + "</b> (" + pois[i].value + " check-ins)<br>" + poi.category.name + ", " + poi.category.zero_category_name
        },
        icon: "/static/profileviewer/images/map_icons/" + poi.category.id + "_black.png"
      });
    }
    _map.fitZoom();
    if(_map.getZoom() > 17){
      _map.setZoom(17);
    }
  }

  function renderMap (poi_groups){
    _map = new GMaps({
      lat: 41.0,
      lng: -100.0,
      div: "map-canvas",
      zoom: 3
    });
    _updateMap(poi_groups);
  }


  function render_charts (){
    _fact = crossfilter(_data);

    var by_week = _fact.dimension(function(c){
      //return year_month(c.created_at);
      return d3.time.week(c.created_at);
    });
    var by_category = _fact.dimension(function(c){
      return c.place.category.name;
    });
    var by_zcate = _fact.dimension(function(c){
      return c.place.category.zero_category_name;
    });
    var by_poi = _fact.dimension(function(c){
      c.place.valueOf = function(){
        return c.place.id;
      };
      return c.place;
    });
    var by_region = _fact.dimension(function(c){
      for(var r in _REGIONS){
        if ((_REGIONS[r].lat[0] < c.place.lat && c.place.lat < _REGIONS[r].lat[1] &&
             _REGIONS[r].lng[0] < c.place.lng && c.place.lng < _REGIONS[r].lng[1] )){
          return r;
        }
      }
      return "Other";
    });
    _created_at = _fact.dimension(function(c){return c.created_at;}); // for checkin exporting

    var checkins_by_week = by_week.group().reduceCount();
    var checkins_by_category = by_category.group().reduceCount();
    var checkins_by_zcate = by_zcate.group().reduceCount();
    var checkins_by_poi = by_poi.group().reduceCount();
    var checkins_by_region = by_region.group().reduceCount();
    _allpois = checkins_by_poi.all();

    function patchGrouper(_chart, excludes){
      if(!excludes) {return;}
      var oldGrouper = _chart.othersGrouper();
      _chart.othersGrouper(function(topRows){
        var allrows = _chart.group().all();
        var rows = allrows.filter(function(g){
          return excludes.some(function(x){
            return x === g.key.valueOf();
          }) && !topRows.some(function(x){
            return x.key.valueOf() === g.key.valueOf();
          });});
        rows.forEach(function(d){topRows.push(d);});
        // Fixes D3 transitions on "Others" slice of pie
        if(typeof(topRows[0].key) === "object"){
          _chart.othersLabel({valueOf: function(){return "Others";}});
        }
        oldGrouper(topRows);
      });
    }

    function levelFilters(level){
      return _filter_set
        .filter(function(f){return f.level === level;})
        .map(function(f){return f.pid || f.name;});
    }

    function updateSpotlight(_chart){
        if(_chart.hasFilter()){
          $(_chart.anchor()).parent().parent().addClass("chart-container-focus");
        }
        else {
          $(_chart.anchor()).parent().parent().removeClass("chart-container-focus");
        }
    }

    var w = $("#chart-zcate-pie").width();
    var zcate_chart = dc.pieChart("#chart-zcate-pie")
      .width(w) // (optional) define chart width, :default = 200
      .height(w) // (optional) define chart height, :default = 200
      .transitionDuration(500) // (optional) define chart transition duration, :default = 350
      .colors(_COLORPALETTE)
      .radius(w / 200 * 90) // define pie radius
      .innerRadius(w / 200 * 40)
      .dimension(by_zcate) // set dimension
      .group(checkins_by_zcate) // set group
      .title(function (obj){
        return obj.data.key + ":  " + obj.data.value + " check-in(s)";
      })
      .renderTitle(true);
    patchGrouper(zcate_chart, levelFilters("z"));
    zcate_chart.on("filtered", function(){
      _updateMap(checkins_by_poi);
      updateSpotlight(zcate_chart);
    });

    w = $("#chart-cate-pie").width();
    var cate_chart = dc.pieChart("#chart-cate-pie")
      .width(w) // (optional) define chart width, :default = 200
      .height(w) // (optional) define chart height, :default = 200
      .transitionDuration(500) // (optional) define chart transition duration, :default = 350
      .colors(_COLORPALETTE)
      .radius(w / 200 * 90) // define pie radius
      .innerRadius(w / 200 * 40)
      .dimension(by_category) // set dimension
      .group(checkins_by_category) // set group
      .slicesCap(10)
      .title(function (obj){
        return obj.data.key + ":  " + obj.data.value + " check-in(s)";
      })
      .renderTitle(true);
    patchGrouper(cate_chart, levelFilters("c"));
    cate_chart.on("filtered", function(){
      _updateMap(checkins_by_poi);
      updateSpotlight(cate_chart);
    });

    w = $("#chart-region-pie").width();
    var region_chart = dc.pieChart("#chart-region-pie")
      .width(w) // (optional) define chart width, :default = 200
      .height(w) // (optional) define chart height, :default = 200
      .transitionDuration(500) // (optional) define chart transition duration, :default = 350
      .colors(_COLORPALETTE)
      .radius(w / 200 * 90) // define pie radius
      .innerRadius(w / 200 * 40)
      .dimension(by_region) // set dimension
      .group(checkins_by_region) // set group
      .slicesCap(10)
      .title(function (obj){
        return obj.data.key + ":  " + obj.data.value + " check-in(s)";
      })
      .renderTitle(true);
    region_chart.on("filtered", function(){
      _updateMap(checkins_by_poi);
      updateSpotlight(region_chart);
    });

    w = $("#chart-poi-pie").width();
    var poi_chart = dc.pieChart("#chart-poi-pie")
      .width(w) // (optional) define chart width, :default = 200
      .height(w) // (optional) define chart height, :default = 200
      .transitionDuration(500) // (optional) define chart transition duration, :default = 350
      .colors(_COLORPALETTE)
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
          return obj.data.key.valueOf();
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
      .renderTitle(true);
    patchGrouper(poi_chart, levelFilters("p"));
    poi_chart.on("filtered", function(chart, filter){
      if (chart.hasFilter(filter)){
        _updateMap({top: function(){ return [{key: filter}]; }});
      }
      else{
        _updateMap(checkins_by_poi);
      }
      updateSpotlight(poi_chart);
    });

    w = $("#chart-timeline").width();
    var timeline_chart = dc.barChart("#chart-timeline")
      .width(w) // (optional) define chart width, :default = 200
      .height(100) // (optional) define chart height, :default = 200
      .transitionDuration(500) // (optional) define chart transition duration, :default = 500
      .dimension(by_week) // set dimension
      .group(checkins_by_week) // set group
      .elasticX(false)
      .x(d3.time.scale().domain([new Date(2009, 0, 1), new Date(2013, 7, 0)]))
      .round(d3.time.week.round)
      .xUnits(d3.time.weeks)
      .renderVerticalGridLines(false)
      .elasticY(false)
      .y(d3.scale.linear().domain([0, 20]))
      .centerBar(true)
      .gap(1)
      .renderHorizontalGridLines(true)
      .renderVerticalGridLines(true)
      .brushOn(true)
      .title(function(d) { return "Value: " + d.value; })
      .renderTitle(true);
    timeline_chart.yAxis().tickValues([0, 5, 10, 15,20]);
    timeline_chart.on("filtered", function(){
      _updateMap(checkins_by_poi);
      updateSpotlight(timeline_chart);
    });

    dc.renderAll();
    renderMap(checkins_by_poi);

    _chartTypeMap = {
      p: poi_chart,
      c: cate_chart,
      z: zcate_chart,
      r: region_chart,
      t: timeline_chart
    };
  }

  function initCharts (hash_id, filter_set) {
    _filter_set = filter_set;
    d3.json(
      "/api/data/checkins?candidate=" + hash_id,
      function(err, json){
        if (err){
          throw "Fail to get data for " + hash_id;
        }
        else{
          _data = json;
          _data.forEach(function (c){
            c.created_at = time_parser(c.created_at);
          });
          render_charts();
        }
      }
    );
  }

  function _focus(topic, chart){
    chart.filter(topic);
  }

  function unfocus(charts){
    if (charts) {
      charts.forEach(function(c){c.filterAll();});
    }
    else {
      dc.filterAll();
    }
    dc.redrawAll();
  }

  function focusTopic(topic, chartType){

    if(chartType === "p"){
      for(var i in _allpois){
        if(topic === _allpois[i].key.name){
          topic = _allpois[i].key;
          break;
        }
      }
    }

    if(["p", "z", "c"].indexOf(chartType) >= 0){
      unfocus([_chartTypeMap.p, _chartTypeMap.c, _chartTypeMap.z]);
    }
    _focus(topic, _chartTypeMap[chartType]);

    dc.redrawAll();
  }

  function filteredRecentCheckins(k){
    return _created_at.top(k);
  }

  return {
    initCharts: initCharts,
    focusTopic: focusTopic,
    unfocus: unfocus,
    filteredRecentCheckins: filteredRecentCheckins
  };
}

  // FOOTER
  if(typeof define === "function" && define.amd) {
    define(["d3", "dc", "crossfilter", "GMaps", "jQuery"], _profileviewer);
  } else if(typeof module === "object" && module.exports) {
    module.exports = _profileviewer(d3, crossfilter, dc, GMaps, jQuery);
  } else {
    this.profileviewer = _profileviewer(d3, crossfilter, dc, GMaps, jQuery);
  }
}
)();
