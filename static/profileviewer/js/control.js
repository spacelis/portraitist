/* eslint-env node, amd */
/* global $ */
/**
File: control.js
Author: SpaceLis
Email: Wen.Li@tudelft.nl
GitHub: http://github.com/spacelis
Description:
    Monitoring user interaction with the page.
*/

(function(){ // Header

function _control($){

  var pow = Math.pow;
  var sqrt = Math.sqrt;

  var loadtime = new Date();
  var pageheight = $(document).height();
  var pagewidth = $(document).width();
  var percentwidth = pagewidth / 100;
  var viewportwidth = Math.max(document.documentElement.clientWidth, window.innerWidth || 0);
  var viewportheight = Math.max(document.documentElement.clientHeight, window.innerHeight || 0);

  var state = {
    m_clicks: 0,
    m_travel: 0,
    viewportwidth: viewportwidth,
    viewportheight: viewportheight,
    pageheight: pageheight,
    pagewidth: pagewidth,
    prev_pos: {PageX: 0, PageY: 0},
    init: true,
    trace: []
  };
  var bar = {
    m_clicks: 3,
    m_travel: pageheight,
    t_int: 15000
  };

  function distance(p1, p2){
    return sqrt(pow(p2.PageX - p1.PageX, 2) + pow(p2.PageY - p1.PageY, 2));
  }

  $(document).click(function(e){
    state.m_clicks += 1;
    state.trace.unshift({
      event: "click",
      position: {"PageX": e.PageX, "PageY": e.PageY},
      timestamp: new Date() - loadtime,
      travel: state.trace[0].travel
    });
  });
  $(document).mousemove(function(e){
    var timestamp = new Date() - loadtime;
    var pos = {PageX: e.pageX, PageY: e.pageY};
    if(state.init){
      state.init = false;
      state.trace.unshift({
        event: "moveto",
        position: pos,
        timestamp: timestamp,
        travel: 0
      });
    } else{
      state.m_travel += distance(pos, state.prev_pos);
      state.prev_pos = pos;
      if(distance(state.trace[0].position, pos) > percentwidth ||
         timestamp - state.trace[0].timestamp > 1000)
      {
        state.trace.unshift({
          event: "moveto",
          position: pos,
          timestamp: timestamp,
          travel: state.m_travel
        });
      }
    }
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
  function getState(){
    return state.trace;  // FIXME this may be unsafe, should be cloned.
  }

  function record(e){
    var len = state.trace.unshift(
      {event: "record",
       position: {PageX: state.trace[0].position.PageX,
                  PageY: state.trace[0].position.PageY},
       timestamp: new Date() - loadtime,
       travel: state.m_travel,
       record: e}
    );
    if(len >= 1500){
      state.trace.splice(1000);
    }
  }

  return {"checked": checked,
          "getState": getState,
          "record": record};
}

if(typeof define === "function" && define.amd) { // FOOTER
  define(["$"], _control);
} else if(typeof module === "object" && module.exports) {
  module.exports = _control($);
} else {
  this.control = _control($);
}})();
