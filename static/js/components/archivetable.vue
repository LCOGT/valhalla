<template>
<div id="table">
  bootstrap table
</div>
</template>
<script>
import * as bstable from 'bootstrap-table';
import moment from 'moment';
import {archiveRoot} from '../archive.js';
export default{
  props: ['requestid'],
  mounted: function(){
    var that = this;
    console.log(archiveRoot)
    $(this.$el).find('#table').bootstrapTable({
      url: archiveRoot + 'frames/?limit=1000&REQNUM=' + this.requestid,
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
      // toolbar: '#table-' + requestId + '-toolbar',
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
  }
}
</script>
<style>
</style>
