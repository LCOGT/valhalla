<template>
<div class="row">
  <div class="col-md-4">
    <thumbnail :frameid="curFrame" width="400" height="400"></thumbnail>
  </div>
  <div class="col-md-8">
    <ul class="nav nav-tabs nav-justified">
      <li :class="{ active: tab === 'details' }" v-on:click="tab = 'details'">
        <a title="Details about the observed request.">Details</a>
      </li>
      <li :class="{ active: tab === 'scheduling' }" v-on:click="tab = 'scheduling'">
        <a title="Scheduling history.">Scheduling</a>
      </li>
      <li :class="{ active: tab === 'visibility' }" v-on:click="tab = 'visibility'">
        <a title="Target Visibility.">Visibility</a>
      </li>
      <li :class="{ active: tab === 'data' }" v-on:click="tab = 'data'">
        <a title="Downloadable data.">Data</a>
      </li>
    </ul>
    <div class="tab-content">
      <div class="tab-pane" :class="{ active: tab === 'details' }">
        <div class="row">
          <div class="col-md-6">
            <h4>Windows</h4>
            <table class="table">
              <thead>
                <tr><td><strong>Start</strong></td><td><strong>End</strong></td></tr>
              </thead>
              <tbody>
                <tr v-for="window in request.windows">
                  <td>{{ window.start }}</td><td>{{ window.end }}</td>
                </tr>
              </tbody>
            </table>
            <h4>Configurations</h4>
            <table class="table table-condensed">
              <thead>
                <tr>
                  <td><strong>Instrument</strong></td><td><strong>Filter</strong></td><td><strong>Exposures</strong></td>
                </tr>
              </thead>
              <tbody>
                <tr v-for="molecule in request.molecules">
                  <td>{{ molecule.instrument_name }}</td>
                  <td>{{ molecule.filter }}</td>
                  <td>{{ molecule.exposure_time }} x {{ molecule.exposure_count }}</td>
                </tr>
              </tbody>
            </table>
            <h4>Constraints</h4>
            <dl class="twocol">
              <span v-for="x, idx in request.constraints">
              <dt v-if="request.constraints[idx]">{{ idx }}</dt>
              <dd v-if="x">{{ x }}</dd>
              </span>
            </dl>
          </div>
          <div class="col-md-6">
            <h4>Target</h4>
            <dl class="twocol">
              <span v-for="x, idx in request.target">
              <dt v-if="request.target[idx]">{{ idx }}</dt>
              <dd v-if="x">{{ x }}</dd>
              </span>
            </dl>
          </div>
        </div>
      </div>
      <div class="tab-pane" :class="{ active: tab === 'data' }">
        <archivetable :requestid="request.id"></archivetable>
      </div>
      <div class="tab-pane" :class="{ active: tab === 'scheduling' }">
        <blockhistory v-show="blockData.length > 0" :data="blockData" :showPlotControls="true"></blockhistory>
      </div>
      <div class="tab-pane" :class="{ active: tab === 'visibility' }">
        <airmass_telescope_states v-show="'airmass_limit' in airmassData" :airmassData="airmassData" :telescopeStatesData="telescopeStatesData"></airmass_telescope_states>
      </div>
    </div>
  </div>
</div>
</template>
<script>
import $ from 'jquery';
import thumbnail from './components/thumbnail.vue';
import archivetable from './components/archivetable.vue';
import blockhistory from './components/blockhistory.vue';
import airmass_telescope_states from './components/airmass_telescope_states.vue';
import {login, getLatestFrame} from './archive.js';

export default {
  name: 'app',
  components: {thumbnail, archivetable, blockhistory, airmass_telescope_states},
  data: function(){
    return {
      request: {},
      curFrame: null,
      blockData: [],
      airmassData: {},
      telescopeStatesData: {},
      tab: 'details',
    };
  },
  created: function(){
    var requestId = $('#request-detail').data('requestid');
    var that = this;
    login(function(){
      $.getJSON('/api/requests/' + requestId, function(data){
        that.request = data;
        if(data.state === 'COMPLETED'){
          getLatestFrame(data.id, function(data){
            that.curFrame = data.id;
          });
        }
      });
    });
  },
  watch: {
    'tab': function(tab){
      if(tab === 'scheduling' && this.blockData.length === 0){
        this.loadBlockData();
      }
      else if (tab === 'visibility'){
        if($.isEmptyObject(this.airmassData)) {
          this.loadAirmassData();
        }
        if($.isEmptyObject(this.telescopeStatesData)){
          this.loadTelescopeStatesData();
        }
      }
    }
  },
  methods: {
    loadBlockData: function(){
      var that = this;
      var requestId = $('#request-detail').data('requestid');
      $.getJSON('/api/requests/' + requestId + '/blocks/', function(data){
        that.blockData = data;
      });
    },
    loadAirmassData: function(){
      var that = this;
      var requestId = $('#request-detail').data('requestid');
      $.getJSON('/api/requests/' + requestId + '/airmass/', function(data){
        that.airmassData = data;
      });
    },
    loadTelescopeStatesData: function(){
      var that = this;
      var requestId = $('#request-detail').data('requestid');
      $.getJSON('/api/requests/' + requestId + '/telescope_states/', function(data){
        that.telescopeStatesData = data;
      });
    }
  }

};
</script>
<style>
dl.twocol {
  -moz-column-count: 2;
  -webkit-column-count: 2;
  column-count: 2;
}
</style>
