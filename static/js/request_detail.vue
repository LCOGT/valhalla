<template>
<div class="row">
  <div class="col-md-4">
    <thumbnail :frameid="curFrame" width="400" height="400"></thumbnail>
  </div>
  <div class="col-md-8">
    <ul class="nav nav-tabs nav-justified col-md-6">
      <li :class="{ active: tab === 1 }" v-on:click="tab = 1">
        <a title="Details about the observed request.">Details</a>
      </li>
      <li :class="{ active: tab === 2 }" v-on:click="tab = 2">
        <a title="Downloadable data.">Data</a>
      </li>
      <li :class="{ active: tab === 3 }" v-on:click="tab = 3">
        <a title="Scheduling history.">Scheduling</a>
      </li>
      <li :class="{ active: tab === 4 }" v-on:click="tab = 4">
        <a title="Target Visibility.">Visibility</a>
      </li>
    </ul>
    <div class="tab-content">
      <div class="tab-pane" :class="{ active: tab === 1 }">
        <div class="row">
          <div class="col-md-6">
            <h4>Windows</h4>
            <table class="table">
              <thead>
                <tr><td>Start</td><td>End</td></tr>
              </thead>
              <tbody>
                <tr v-for="window in request.windows"><td>{{ window.start }}</td><td>{{ window.end }}</td></tr>
              </tbody>
            </table>
            <h4>Configurations</h4>
            <table class="table table-condensed">
              <thead>
                <tr><td>Instrument</td><td>Filter</td><td>Exposures</td></tr>
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
      <div class="tab-pane" :class="{ active: tab === 2 }">
        <archivetable :requestid="request.id"></archivetable>
      </div>
      <div class="tab-pane" :class="{ active: tab === 3 }">
      </div>
      <div class="tab-pane" :class="{ active: tab === 4 }">
      </div>
    </div>
  </div>
</div>
</template>
<script>
import $ from 'jquery';
import thumbnail from './components/thumbnail.vue';
import archivetable from './components/archivetable.vue';
import {login, getLatestFrame} from './archive.js';

export default {
  name: 'app',
  components: {thumbnail, archivetable},
  data: function(){
    return {
      request: {},
      curFrame: null,
      tab: 1,
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

};
</script>
<style>
dl.twocol {
  -moz-column-count: 2;
  -webkit-column-count: 2;
  column-count: 2;
}
</style>
