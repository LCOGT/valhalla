import $ from 'jquery';
import moment from 'moment';
import {datetimeFormat} from './utils.js';

import {getThumbnail, getLatestFrame, downloadAll} from './archive.js';

$('#downloadall').click(function(){
  downloadAll($(this).data('requestid'));
});

$(document).ready(function(){
  $('.thumbnail-small').each(function(idx, elem){
    getLatestFrame($(elem).data('request'), function(frame){
      $(elem).fadeOut(200);
      $(elem).prev().show().html('<center><span class="fa fa-spinner fa-spin"></span></center>');
      getThumbnail(frame.id, 75, function(data){
        if(data.error){
          $(elem).prev().html(data.error);
        }else{
          $(elem).attr('src', data.url).show();
          $(elem).prev().hide();
        }
      });
    });
  });

  $('.pending-details').each(function(){
    var that = $(this);
    var requestId = $(this).data('request');
    $.getJSON('/api/requests/' + requestId + '/blocks/?canceled=false', function(data){
      var content = '';
      if(data.length > 0){
        data = data.reverse(); // get the latest non cancled block
        content = 'Scheduled for<br/>' + data[0].start + ' to ' +
          data[0].end + '<br/>Site: ' + data[0].site;
        content = 'Scheduled at ' + data[0].site + ' between ' + moment(data[0].start).format(datetimeFormat) +
          ' and ' + moment(data[0].end).format(datetimeFormat);
      }else{
        content = 'No scheduling information found';
      }
      that.html(content);
    });
  });
});
