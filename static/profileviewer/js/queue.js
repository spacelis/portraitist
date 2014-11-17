/* eslint-env node, amd */
/* global $ */
/**
File: queue.js
Author: SpaceLis
Email: Wen.Li@tudelft.nl
GitHub: http://github.com/spacelis
Description:
  A task queue that can be useful for gathering data from a bunch of requests.
*/

(function(){ // Header

function _queue($){

  /**
   * processing tasks in sequence and return the results
   */
  function request(url, acc, finalize, progress){
      $.ajax(url).done(function(ret){
        if(typeof(progress) === "function"){
          progress();
        }
        if(ret.more){
          request(ret.next, acc.concat(ret.data), finalize, progress);
        }
        else {
          finalize(acc.concat(ret.data));
        }
      }).fail(function(){
        throw "Failed at " + url;
      });
  }

  function map(urls, func){
    for(var i in urls){
      $.ajax(urls[i]).done(function(data){ func(data, i); });
    }
  }

  return {
    request: request,
    map: map
  };
}

if(typeof define === "function" && define.amd) { // FOOTER
  define(["$"], _queue);
} else if(typeof module === "object" && module.exports) {
  module.exports = _queue($);
} else {
  this.queue = _queue($);
}})();
