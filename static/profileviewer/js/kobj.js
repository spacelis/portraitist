/* global ko */
var kobj = (function(){
  this.flattened = function(ob) {
    var toReturn = {};
    
    for (var i in ob) {
      if (!ob.hasOwnProperty(i)) {
        continue;
      }
      
      if ((typeof ob[i]) === 'object') {
        var flatObject = this.flattened(ob[i]);
        for (var x in flatObject) {
          if (!flatObject.hasOwnProperty(x)) {
            continue;
          }
          
          toReturn[i + '_' + x] = flatObject[x];
        }
      } else {
        toReturn[i] = ob[i];
      }
    }
    return toReturn;
  };
  this.buildFrom = function(jobj){
    var fobj = this.flattened(jobj);
    var kview = {};
    for (var i in fobj) {
      kview[i] = ko.observable(fobj[i]);
    }
    return kview;
  };
  this.merge = function(kobj, jobj){
    $.extend(kobj, this.buildFrom(jobj));
  };
  return this;
}());
