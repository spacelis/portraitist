/* global ko */
var KnockObj = (function(){
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
  this.update = function(kobj, jobj){
    for(var i in jobj){
      if (kobj[i]){
        kobj[i](jobj[i]);
      }
      else {
        throw new Error("Key `" + i + "` doesn't exist for update.");
      }
    }
  };
  this.bindCookie = function(view_model, key, options){
    if (view_model[key]){
      view_model[key].subscribe(function(v){
        $.cookie(key, v, options);
      });
    }
  };
  return this;
}());
