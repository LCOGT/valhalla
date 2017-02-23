import $ from 'jquery';

export {cancelUserRequest};

function cancelUserRequest(id) {
  if(confirm('Cancel this request? This action cannot be undone')){
    $.ajax({
      type: 'PUT',
      url: '/api/userrequests/' + id + '/cancel/',
      contentType: 'application/json',
    }).done(function(){
      window.location = '/userrequests/' + id + '/';
    }).fail(function(data){
      alert(data.responseJSON.errors[0]);
    });
  }
}
