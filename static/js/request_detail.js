import $ from 'jquery';
import Vue from 'vue';

import {getThumbnail, getLatestFrame, downloadAll} from './archive.js';
import App from './request_detail.vue';

new Vue({
  el: '#app',
  render: function(h){
    return h(App);
  }
});

$('#downloadall').click(function(){
  downloadAll($(this).data('requestid'));
});

$(document).ready(function(){
  $('.thumbnail-small').each(function(idx, elem){
    getLatestFrame($(elem).data('request'), function(frame){
      $(elem).fadeOut(200);
      $(elem).prev().show().html('<center><span class="fa fa-spinner fa-spin"></span></center>');
      getThumbnail(frame.id, 100, function(data){
        if(data.error){
          $(elem).prev().html(data.error);
        }else{
          $(elem).attr('src', data.url).show();
          $(elem).prev().hide();
        }
      });
    });
  });
});

