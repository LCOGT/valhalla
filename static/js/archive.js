/* globals $ */
/* eslint-disable no-undef */
var archiveRoot = 'https://archive-api.lco.global/';

$.ajaxPrefilter(function(options, originalOptions, jqXHR){
  if(options.url.indexOf(archiveRoot)>= 0 || options.url.indexOf('thumbnails.lco.global/')>= 0 ){
    jqXHR.setRequestHeader('Authorization', 'Token ' + localStorage.getItem('authToken'));
  }
});


login = function(bearer, callback){
  if(localStorage.getItem('authToken')){
    callback();
  }else{
    $.ajax({
      url: archiveRoot + 'api-token-auth/',
      type: 'post',
      data: {},
      headers: {'Authorization': 'Bearer ' + bearer},
      dataType: 'json',
      success: function(data){
        localStorage.setItem('authToken', data.token);
        callback();
      }
    });
  }
};

downloadZip = function(frameIds){
  var postData = {};
  for(var i = 0; i < frameIds.length; i++){
    postData['frame_ids[' + i + ']'] = frameIds[i];
  }
  postData['auth_token'] = localStorage.getItem('authToken');
  $.fileDownload(archiveRoot + 'frames/zip/', {
    httpMethod: 'POST',
    data: postData
  });
};

downloadAll = function(requestId){
  $.getJSON(archiveRoot + 'frames/?limit=1000&REQNUM=' + requestId, function(data){
    if(data.count > 1000){
      alert('Over 1000 products found. Please use https://archive.lco.global to download your data');
      return false;
    }
    frameIds = [];
    for (var i = 0; i < data.results.length; i++) {
      frameIds.push(data.results[i].id);
    }
    downloadZip(frameIds);
  });
};

getThumbnail = function(frameId, size, callback){
  $.getJSON('https://thumbnails.lco.global/' + frameId + '/?width=' + size + '&height=' + size, function(data){
    callback(data);
  });
};

getLatestFrame = function(requestId, callback){
  $.getJSON(archiveRoot + 'frames/?ordering=-id&limit=1&REQNUM=' + requestId, function(data){
    callback(data.results[0]);
  });
};
