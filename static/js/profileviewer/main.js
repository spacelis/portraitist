function init_map(){
  $('#map-canvas').initMap(map_data);
}

function init_cate_pie() {
  var data = google.visualization.arrayToDataTable(cate_pie_data);

  var options = {
    //title: 'Category distribution'
  };

  var chart = new google.visualization.PieChart(
      document.getElementById('chart-cate-pie'));
  chart.draw(data, options);
}

function init_cate_timelines() {
  var data = google.visualization.arrayToDataTable(cate_timelines_data);

  var options = {
    title: 'Company Performance',
    hAxis: {title: 'Time',  titleTextStyle: {color: 'red'}},
    isStacked: true
  };

  var chart = new google.visualization.ColumnChart(
      document.getElementById('chart-cate-timeline'));
  chart.draw(data, options);
}


function init_poi_pie() {
  var data = google.visualization.arrayToDataTable(poi_pie_data);

  var options = {
    //title: 'Category distribution'
  };

  var chart = new google.visualization.PieChart(
      document.getElementById('chart-poi-pie'));
  chart.draw(data, options);
}
