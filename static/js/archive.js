import $ from 'jquery';
import 'jquery-file-download';
export const archiveRoot = 'https://archive-api.lco.global/';
export const archiveUIRoot = 'https://archive.lco.global/';
export {archiveAjaxSetup, login, downloadZip, downloadAll, getThumbnail, getLatestFrame};

function archiveAjaxSetup(){
  login(function(){
    $.ajaxPrefilter(function(options, originalOptions, jqXHR){
      if(options.url.indexOf(archiveRoot)>= 0 || options.url.indexOf('thumbnails.lco.global/')>= 0 ){
        jqXHR.setRequestHeader('Authorization', 'Token ' + localStorage.getItem('archiveAuthToken'));
      }
    });
  });
}

function login(callback){
  if(localStorage.getItem('archiveAuthToken')){
    callback();
  }else{
    var bearer = '';
    $.getJSON('/api/profile/', function(data){
      bearer = data.tokens.archive;
    }).done(function(){
      $.ajax({
        url: archiveRoot + 'api-token-auth/',
        type: 'post',
        data: {},
        headers: {'Authorization': 'Bearer ' + bearer},
        dataType: 'json',
        success: function(data){
          localStorage.setItem('archiveAuthToken', data.token);
          callback();
        }
      });
    });
  }
}

function downloadZip(frameIds){
  var postData = {};
  for(var i = 0; i < frameIds.length; i++){
    postData['frame_ids[' + i + ']'] = frameIds[i];
  }
  postData['auth_token'] = localStorage.getItem('archiveAuthToken');
  $.fileDownload(archiveRoot + 'frames/zip/', {
    httpMethod: 'POST',
    data: postData
  });
}

function downloadAll(requestId){
  $.getJSON(archiveRoot + 'frames/?limit=1000&REQNUM=' + requestId, function(data){
    if(data.count > 1000){
      alert('Over 1000 products found. Please use https://archive.lco.global to download your data');
      return false;
    }
    var frameIds = [];
    for (var i = 0; i < data.results.length; i++) {
      frameIds.push(data.results[i].id);
    }
    downloadZip(frameIds);
  });
}

function getThumbnail(frameId, size, callback){
  $.getJSON('https://thumbnails.lco.global/' + frameId + '/?width=' + size + '&height=' + size, function(data){
    callback(data);
  }).fail(function(){
    callback({'error': '<span>Could not load thumbnail for this file</span>'});
  });
}

function getLatestFrame(requestId, callback){
  $.getJSON(archiveRoot + 'frames/?ordering=-id&limit=1&REQNUM=' + requestId, function(data){
    callback(data.results[0]);
  });
}
