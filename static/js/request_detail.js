/* globals $ */
/* eslint-disable no-undef */
showDetails = function(requestId){
  $('#request-show-' + requestId).find('i').toggleClass('fa-flip-vertical');
  $('#request-detail-' + requestId).slideToggle();
  getTableData(requestId);
};

downloadSelected = function(requestId){
  var table = $('#data-' + requestId).find('table.frame-list');
  var frameIds = [];
  selections = table.bootstrapTable('getSelections');
  for(var i = 0; i < selections.length; i++){
    frameIds.push(selections[i].id);
  }
  downloadZip(frameIds);

};

setThumb = function(frameid, elem, size){
  elem.fadeOut(200);
  elem.prev().show().html('<center><span class="fa fa-spinner fa-spin"></span></center>');
  getThumbnail(frameid, size, function(data){
    if(data.error){
      elem.prev().html(data.error);
    }else{
      elem.attr('src', data.url).show();
      elem.prev().hide();
    }
  });
};

getTableData = function(requestId){
  var table = $('#data-' + requestId).find('table.frame-list');
  table.bootstrapTable({
    url: archiveRoot + 'frames/?limit=1000&REQNUM=' + requestId,
    responseHandler: function(res){
      if(res.count > 1000){
        alert('More than 1000 results found, please view on archive to view all data');
      }
      return res.results;
    },
    queryParamsType: '',
    idField: 'id',
    pagination: true,
    pageSize: 15,
    sortName: 'RLEVEL',
    sortOrder: 'desc',
    maintainSelected: true,
    checkboxHeader: true,
    toolbar: '#table-' + requestId + '-toolbar',
    columns: [{
      field: 'state',
      title: '',
      checkbox: true,
    },{
      field: 'filename',
      title: 'filename',
      sortable: 'true',
    },{
      field: 'DATE_OBS',
      title: 'date_obs',
      sortable: 'true',
      formatter: function(value){
        return moment.utc(value, 'YYYY-MM-DDTHH:mm:ssZ').format('YYYY-MM-DD HH:mm:ss');
      }
    },{
      field: 'FILTER',
      title: 'filter',
      sortable: 'true',
    },{
      field: 'OBSTYPE',
      title: 'obstype',
      sortable: 'true',
    },{
      field: 'RLEVEL',
      title: 'r. level',
      sortable: 'true',
    }]
  });
};
