/* global $ */

var control = (function(){
  var pow = Math.pow;
  var sqrt = Math.sqrt;

  var pageheight = $(document).height();
  var loadtime = new Date();

  var state = {m_clicks: 0,
               m_travel: 0,
               prev_x: 0,
               prev_y: 0,
               init: true};
  var bar = {
    m_clicks: 3,
    m_travel: pageheight,
    t_int: 15000,
  };
  $(document).click(function(e){
    state.m_clicks += 1;
  });
  $(document).mousemove(function(e){
    var x = e.pageX, y = e.pageY;
    if(state.init){
      state.init = false;
    } else{
      state.m_travel += sqrt(pow(x - state.prev_x, 2) + pow(y - state.prev_y, 2));
    }
    state.prev_x = x;
    state.prev_y = y;
  });

  function mouseState(){
    return (state.m_clicks >= bar.m_clicks && state.m_travel >= bar.m_travel);
  }
  function physicalState(){
    return (new Date() - loadtime >= bar.t_int);
  }

  function checked(){
    return (mouseState() && physicalState());
  }

  return {'checked': checked};
}());
