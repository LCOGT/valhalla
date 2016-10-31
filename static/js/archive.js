var archiveRoot = 'https://archive-api.lco.global/'

$.ajaxPrefilter(function(options, originalOptions, jqXHR){
  if(options.url.indexOf(archiveRoot) || options.url.indexOf('thumbnails.lco.global/')>= 0 ){
      jqXHR.setRequestHeader('Authorization', 'Token ' + localStorage.getItem('authToken'));
  }
});


login = function(bearer, callback){
  if(localStorage.getItem('authToken')){
    callback()
  }else{
    $.ajax({
        url: archiveRoot + 'api-token-auth/',
        type: 'post',
        data: {},
        headers: {'Authorization': 'Bearer ' + bearer},
        dataType: 'json',
        success: function(data){
          localStorage.setItem('authToken', data.token)
          callback()
        }
    });
  }
}

downloadZip = function(frameIds){
  var postData = {}
  for(var i = 0; i < frameIds.length; i++){
      postData['frame_ids[' + i + ']'] = frameIds[i];
  }
  postData['auth_token'] = localStorage.getItem('authToken')
  $.fileDownload(archiveRoot + 'frames/zip/', {
    httpMethod: 'POST',
    data: postData
  });
}
