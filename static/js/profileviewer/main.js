function sum (arr) {
  var s = 0;
  for (var i = arr.length - 1; i >= 0; i--) {
    s += arr[i];
  }
  return s;
}


function init_map(map_data){
  var data = {center: [41, -100], options: {zoom: 4}};
  var markers = {};
  for(var i in map_data) {
    var poi = map_data[i];
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
}


function init_cate_pie(cate_timeline_data) {
  var piedata = [['Category', '# of Check-ins']];
  for (var i in cate_timeline_data) {
    piedata.push([i, sum(cate_timeline_data[i])]);
  }
  var data = google.visualization.arrayToDataTable(piedata);

  var options = {
    //title: 'Category distribution'
  };

  var chart = new google.visualization.PieChart(
      document.getElementById('chart-cate-pie'));
  chart.draw(data, options);
}


function init_cate_timelines(cate_timelines_data) {
  var tldata = [['# of Check-ins']];
  var i;
  for(i in cate_timelines_data) {
    tldata[0].push(i);
  }
  for(i in cate_timelines_data[Object.keys(cate_timelines_data)[0]]){
    var s = [i,];
    for(var j in cate_timelines_data) {
      s.push(cate_timelines_data[j][i]);
    }
    tldata.push(s);
  }
  var data = google.visualization.arrayToDataTable(tldata);

  var options = {
    title: 'Category Timelines',
    hAxis: {title: 'Months ago',  titleTextStyle: {color: 'red'}},
    isStacked: true
  };

  var chart = new google.visualization.ColumnChart(
      document.getElementById('chart-cate-timeline'));
  chart.draw(data, options);
}


function init_poi_pie(poi_timelines_data) {
  var piedata = [['POI', '# of Check-ins']];
  for (var i in poi_timelines_data) {
    piedata.push(['['+ poi_timelines_data[i].category + ']' + poi_timelines_data[i].name,
                  sum(poi_timelines_data[i].timeline)]);
  }
  var data = google.visualization.arrayToDataTable(piedata);

  var options = {
    //title: 'Category distribution'
  };

  var chart = new google.visualization.PieChart(
      document.getElementById('chart-poi-pie'));
  chart.draw(data, options);
}


function init_poi_timelines(poi_timelines_data) {
  var tldata = [['# of Check-ins']];
  var i;
  for(i in poi_timelines_data) {
    tldata[0].push('['+ poi_timelines_data[i].category + ']' + poi_timelines_data[i].name);
  }
  for(i in poi_timelines_data[Object.keys(poi_timelines_data)[0]].timeline){
    var s = [i,];
    for(var j in poi_timelines_data) {
      s.push(poi_timelines_data[j].timeline[i]);
    }
    tldata.push(s);
  }
  var data = google.visualization.arrayToDataTable(tldata);

  var options = {
    title: 'POI timelines',
    hAxis: {title: 'Month(s) ago',  titleTextStyle: {color: 'red'}},
    isStacked: true
  };

  var chart = new google.visualization.ColumnChart(
      document.getElementById('chart-poi-timeline'));
  chart.draw(data, options);
}
