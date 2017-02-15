<template>
<div>
  <div id="archive-table-toolbar">
    <button v-on:click="downloadSelected" class="btn btn-default btn-sm">
      <i class="fa fa-check"></i> Download Selected
    </button>
    <button v-on:click="downloadAll" class="btn btn-default btn-sm">
      <i class="fa fa-download"></i> Download All
    </button>
    <a class="btn btn-default btn-sm" target="_blank" :href="archiveLink">
      <i class="fa fa-arrow-right"></i> View on Archive
    </a>
  </div>
  <table id="archive-table"></table>
</div>
</template>
<script>
import 'bootstrap-table';
import $ from 'jquery';
import moment from 'moment';
import {datetimeFormat} from '../utils.js';
import {archiveRoot, archiveUIRoot, downloadAll, downloadZip} from '../archive.js';
export default{
  props: ['requestid'],
  watch: {
    requestid: function(){
      $('#archive-table').bootstrapTable('refresh',
        {url: archiveRoot + 'frames/?limit=1000&REQNUM=' + this.requestid}
      );
    }
  },
  methods: {
    downloadSelected: function(){
      var frameIds = [];
      var selections = $('#archive-table').bootstrapTable('getSelections');
      for(var i = 0; i < selections.length; i++){
        frameIds.push(selections[i].id);
      }
      downloadZip(frameIds);
    },
    downloadAll: function(){
      downloadAll(this.requestid);
    }
  },
  computed: {
    archiveLink: function(){
      return archiveUIRoot + '?REQNUM=' + this.requestid;
    }
  },
  mounted: function(){
    $('#archive-table').bootstrapTable({
      url: null,
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
      toolbar: '#archive-table-toolbar',
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
        title: 'DATE_OBS',
        sortable: 'true',
        formatter: function(value){
          return moment.utc(value, 'YYYY-MM-DDTHH:mm:ssZ').format(datetimeFormat);
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
};
</script>
