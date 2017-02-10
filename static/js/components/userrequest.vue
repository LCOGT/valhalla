<template>
  <panel id="general" :errors="errors" v-on:show="show = $event" :canremove="false" :cancopy="false"
         icon="fa-id-card-o" title="General Information" :show="show">
    <div v-for="error in errors.non_field_errors" class="alert alert-danger" role="alert">{{ error }}</div>
      <div class="row">
        <div class="col-md-6 compose-help" v-show="show">
          <h3>Duration of Observing Request:</h3>
          <h2>{{ durationDisplay }}</h2>
          <br/>
          <ul>
            <li>
              <a href="https://lco.global/documentation/">More information about Rapid Response mode.</a>
            </li>
            <li>
              <a target="_blank" href="https://lco.global/files/User_Documentation/the_new_priority_factor.pdf">
                More information about IPP.
              </a>
            </li>
          </ul>
        </div>
        <div :class="show ? 'col-md-6' : 'col-md-12'">
          <form class="form-horizontal">
            <customfield v-model="userrequest.group_id" label="Title" field="title" v-on:input="update"             :errors="errors.group_id" desc="Provide a name for this observing request.">
            </customfield>
            <customselect v-model="userrequest.proposal" label="Proposal" field="proposal"
                          v-on:input="update" :errors="errors.proposal" :options="proposalOptions"
                          desc="Select the proposal for which this observation will be made.">
            </customselect>
            <customselect v-model="userrequest.observation_type" label="Mode"
                          field="observation_type" v-on:input="update"
                          :errors="errors.observation_type"
                          :options="[{value: 'NORMAL', text: 'Queue scheduled (default)'},
                                     {value:'TARGET_OF_OPPORTUNITY', text: 'Rapid Response'}]"
                          desc="Rapid response mode means the request should be executed immediately.">
            </customselect>
            <customfield v-model="userrequest.ipp_value" label="Ipp Factor" field="ipp_value"
                         v-on:input="update" :errors="errors.ipp_value"
                         desc="Provide an InterProposal Priority factor for this request. Acceptable values are between 0.5 and 2.0">
            </customfield>
            <div class="collapse-inline" v-show="!show">Total Duration: <strong>{{ durationDisplay }}</strong></div>
          </form>
        </div>
      </div>
      <div v-for="(request, idx) in userrequest.requests">
        <modal :show="showCadence" v-on:close="cancelCadence" v-on:submit="acceptCadence" header="Generated Cadence">
          <p>The blocks below represent the windows of the requests that will be generated if the current cadence is accepted.
          Press cancel to discard the cadence. Once a cadence is accepted, the individual generated requests may be edited.</p>
          <cadence :data="cadenceRequests"></cadence>
        </modal>
        <request :index="idx" :request="request" :available_instruments="available_instruments" :parentshow="show"
                 v-on:requestupdate="requestUpdated" v-on:cadence="expandCadence"
                 :errors="_.get(errors, ['requests', idx], {})"
                 :duration_data="_.get(duration_data, ['requests', idx], {'duration': 0})"
                 v-on:remove="removeRequest(idx)" v-on:copy="addRequest(idx)">
        </request>
        <div class="request-margin"></div>
      </div>
    </div>
  </panel>
</template>
<script>
import $ from 'jquery';
import _ from 'lodash';
import moment from 'moment';

import modal from './util/modal.vue';
import request from './request.vue';
import cadence from './cadence.vue';
import panel from './util/panel.vue';
import customfield from './util/customfield.vue';
import customselect from './util/customselect.vue';

export default {
  props: ['errors', 'userrequest', 'duration_data'],
  components: {request, cadence, modal, customfield, customselect, panel},
  data: function(){
    return {
      show: true,
      showCadence: false,
      cadenceRequests: [],
      available_instruments: {},
      proposals: [],
      cadenceRequestId: -1
    };
  },
  created: function(){
    var that = this;
    var allowed_instruments = {};
    $.getJSON('/api/profile/', function(data){
      that.proposals = data.proposals;
      for(var ai in data.available_instrument_types){
        allowed_instruments[data.available_instrument_types[ai]] = {};
      }
    }).done(function(){
      $.getJSON('/api/instruments/', function(data){
        for(var ai in allowed_instruments){
          allowed_instruments[ai] = data[ai];
        }
        that.available_instruments = allowed_instruments;
        that.update();
      });
    });
  },
  computed:{
    proposalOptions: function(){
      return _.sortBy(_.map(this.proposals, function(p){return {'value': p, 'text': p};}), 'text');
    },
    durationDisplay: function(){
      var duration =  moment.duration(this.duration_data.duration, 'seconds');
      return duration.hours() + ' hrs ' + duration.minutes() + ' min ' + duration.seconds() + ' sec';
    }
  },
  watch: {
    'userrequest.requests.length': function(value){
      this.userrequest.operator = value > 1 ? 'MANY' : 'SINGLE';
    }
  },
  methods: {
    update: function(){
      this.$emit('userrequestupdate');
    },
    requestUpdated: function(){
      console.log('request updated');
      this.update();
    },
    addRequest: function(idx){
      var newRequest = _.cloneDeep(this.userrequest.requests[idx]);
      this.userrequest.requests.push(newRequest);
      this.update();
    },
    removeRequest: function(idx){
      this.userrequest.requests.splice(idx, 1);
      this.update();
    },
    expandCadence: function(data){
      if(!_.isEmpty(this.errors)){
        alert('Please make sure your request is valid before generating a cadence');
        return false;
      }
      this.cadenceRequestId = data.id;
      var payload = _.cloneDeep(this.userrequest);
      payload.requests = [_.cloneDeep(data.request)];
      payload.requests[0].windows = [];
      payload.requests[0].cadence = data.cadence;
      var that = this;
      $.ajax({
        type: 'POST',
        url: '/api/user_requests/cadence/',
        data: JSON.stringify(payload),
        contentType: 'application/json',
        success: function(data){
          for(var r in data.requests){
            that.cadenceRequests.push(data.requests[r]);
          }
        }
      });
      this.showCadence = true;
    },
    cancelCadence: function(){
      this.cadenceRequests = [];
      this.cadenceRequestId = -1;
      this.showCadence = false;
    },
    acceptCadence: function(){
      // this is a bit hacky because the UI representation of a request doesnt match what the api expects/returns
      var that = this;
      for(var r in this.cadenceRequests){
        // all that changes in the cadence is the window, so instead of parsing what is returned we just copy the request
        // that the cadence was generated from and replace the window from what is returned.
        var newRequest = _.cloneDeep(that.userrequest.requests[that.cadenceRequestId]);
        newRequest.windows = that.cadenceRequests[r].windows;
        delete newRequest.cadence;
        that.userrequest.requests.push(newRequest);
      }
      // finally we remove the original request
      this.removeRequest(that.cadenceRequestId);
      if(this.userrequest.requests.length > 1) this.userrequest.operator = 'MANY';
      this.cadenceRequests = [];
      this.cadenceRequestId = -1;
      this.showCadence = false;
      this.update();
    }
  }
};
</script>
