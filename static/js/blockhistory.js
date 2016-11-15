/* globals vis $ */
/* eslint-disable no-undef */

create_blockhistory_plot = function(request_number, data){

  if(data.length == 0){
    $('#' + request_number + '-bh-loading').hide();
    $('#' + request_number + '-bh-legend').hide();
    $('#' + request_number + '-blockhistory-plot-title').text('Request has never been scheduled');
    $('#' + request_number + '-blockhistory-plot-controls').hide();
    return;
  }

  var groups = new vis.DataSet();
  var items = new vis.DataSet();

  var previousBlock = data[0];
  var previousBlockIndex = 1;
  var index = 0;

  for(var i = 0; i < data.length; i++){
    var block = data[i];
    block.start += 'Z';
    block.end += 'Z';
    var state = '';
    if(block.completed) state += ' COMPLETED';
    else if(block.failed){
      state += ' FAILED';
      block.fail_reason = '<br/>' + block.fail_reason;
    }
    else if(block.attempted) state += ' ATTEMPTED';
    else if(block.canceled) state += ' CANCELED';
    else if(new Date(block.end) < new Date().getTime()) state += 'SCHEDULED-PAST';
    else state += 'SCHEDULED';

    block.state = state;
    
    if (block.cancel_date != null){
      block.cancel_date = '<br/>canceled: ' + block.cancel_date.replace('T', ' ');
    }
    else{
      block.cancel_date = '';
    }
    if(block.start != previousBlock.start || block.site != previousBlock.site || block.state != previousBlock.state
      || block.observatory != previousBlock.observatory || block.telescope != previousBlock.telescope){

      var className = 'timeline_block ' + previousBlock.state;

      groups.add({id: index, content: previousBlockIndex});

      items.add({
        id: index,
        group: index,
        title: 'telescope: ' + previousBlock.site + '.' +  previousBlock.observatory + '.' + previousBlock.telescope + previousBlock.fail_reason + previousBlock.cancel_date + '<br/>start: ' + previousBlock.start.replace('T', ' ') + '<br/>end: ' + previousBlock.end.replace('T', ' '),
        className: className,
        start: previousBlock.start,
        end: previousBlock.end,
        toggle: 'tooltip',
        html: true,
        type: 'range'
      });
      index++;
      previousBlockIndex = i+1;
    }
    previousBlock = block;
  }

  groups.add({id: index, content: previousBlockIndex});

  items.add({
    id: index,
    group: index,
    title: 'telescope: ' + previousBlock.site + '.' +  previousBlock.observatory + '.' + previousBlock.telescope + previousBlock.fail_reason + previousBlock.cancel_date + '<br/>start: ' + previousBlock.start.replace('T', ' ') + '<br/>end: ' + previousBlock.end.replace('T', ' '),
    className: 'timeline_block ' + previousBlock.state,
    start: previousBlock.start,
    end: previousBlock.end,
    toggle: 'tooltip',
    html: true,
    type: 'range'
  });
  index++;

  var maxTime = new Date(items.max('end')['end']);
  var minTime = new Date(items.min('start')['start']);

  var options = {
    groupOrder: 'content',
    maxHeight: '450px',
    align: 'right',
    dataAttributes: ['toggle', 'html'],
    selectable: false,
    snap: null,
    min: new Date(minTime.getTime() - 30*60000),
    max: new Date(maxTime.getTime() + 30*60000),
    zoomKey: 'ctrlKey',
    moment: function(date){
      return vis.moment(date).utc();
    }
  };
  var container = document.getElementById(request_number + '-blockhistory-plot');
  var timeline = new vis.Timeline(container);
  timeline.setOptions(options);
  timeline.setGroups(groups);
  timeline.setItems(items);


  var timeline_min = new Date(items.get(index-1)['start']);
  var timeline_max = new Date(items.get(index-1)['end']);
  if (index > 12){
    for (var i = index-1; i >= index - 12; i--){
      var start = new Date(items.get(i)['start']);
      var end = new Date(items.get(i)['end']);
      if(start < timeline_min){
        timeline_min = start;
      }
      if(end > timeline_max){
        timeline_max = end;
      }
    }
    timeline_max.setMinutes(timeline_max.getMinutes() + 30);
    timeline_min.setMinutes(timeline_min.getMinutes() - 30);

    //set the initial plot bounds to the last 12 items
    timeline.setWindow(timeline_min, timeline_max);
  }

  $('#' + request_number + '-bh-loading').hide();

  //HAX
  $('.vis-group').mouseover(function(){
    $('.vis-item').tooltip({container: 'body'});
  });

  $('#' + request_number + '-blockhistory-zoom-in' + ', #' + request_number + '-blockhistory-zoom-out').click(function(){
    var range = timeline.getWindow();
    var interval = range.end - range.start;
    var percentage = parseFloat($(this).data('percentage'));

    timeline.setWindow({
      start: range.start.valueOf() - interval * percentage,
      end:   range.end.valueOf()   + interval * percentage
    });
  });

  data['plot'] = timeline;
};

