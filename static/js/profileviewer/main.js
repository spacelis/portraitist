/* global dc */
/* global d3 */
/* global crossfilter */

var profileviewer_ns = (function(){
  var init_map = function (pois){
    var data = {center: [41, -100], options: {zoom: 3}};
    var markers = {};
    for(var i in pois) {
      var poi = pois[i];
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

  var time_parser = d3.time.format("%Y-%m-%dT%H:%M:%S").parse;


  var data;  // holding the data for visualization


  var render_charts = function (){
    //var cate_tl = dc.pieChart('#chart-cate-timeline');
    //var poi_pie = dc.pieChart('#chart-poi-pie');
    //var poi_tl = dc.pieChart('#chart-poi-timeline');

    var fact = crossfilter(data);

    var by_week = fact.dimension(function(c){
      return d3.time.week(c.created_at);
    });
    var by_category = fact.dimension(function(c){
      return c.place.zcate;
    });
    var by_poi = fact.dimension(function(c){
      //return c.place.id + "\t" + c.place.name;
      
      return {
        pid: c.place.id,
        name: c.place.name,
        valueOf: function(){
          return c.place.name;
        }
      };
    });


    var checkins_by_week = by_week.group().reduceCount();
    var checkins_by_category = by_category.group().reduceCount();
    var checkins_by_poi = by_poi.group().reduceCount();



    dc.pieChart('#chart-cate-pie')
      .width(200) // (optional) define chart width, :default = 200
      .height(200) // (optional) define chart height, :default = 200
      .transitionDuration(500) // (optional) define chart transition duration, :default = 350
      // (optional) define color array for slices
      .colors(d3.scale.category20())
      //// (optional) define color domain to match your data domain if you want to bind data or color
      //.colorDomain([-1750, 1644])
      //// (optional) define color value accessor
      //.colorAccessor(function(d, i){return d.value;})
      .radius(90) // define pie radius
      // (optional) if inner radius is used then a donut chart will
      // be generated instead of pie chart
      .innerRadius(40)
      .dimension(by_category) // set dimension
      .group(checkins_by_category) // set group
      // (optional) whether chart should render titles, :default = false
      .renderTitle(true);

    dc.pieChart('#chart-poi-pie')
      .width(200) // (optional) define chart width, :default = 200
      .height(200) // (optional) define chart height, :default = 200
      .transitionDuration(500) // (optional) define chart transition duration, :default = 350
      // (optional) define color array for slices
      .colors(d3.scale.category20())
      //// (optional) define color domain to match your data domain if you want to bind data or color
      //.colorDomain([-1750, 1644])
      //// (optional) define color value accessor
      //.colorAccessor(function(d, i){return d.value;})
      .radius(90) // define pie radius
      // (optional) if inner radius is used then a donut chart will
      // be generated instead of pie chart
      .innerRadius(40)
      .dimension(by_poi) // set dimension
      .group(checkins_by_poi) // set group
      .label(function (obj){
        return obj.data.key.name;
      })
      .slicesCap(10)
      .othersLabel('Others')
      // (optional) whether chart should render titles, :default = false
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
