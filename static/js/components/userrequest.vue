<template>
  <div class="row userrequestc" id="general">
    <div class="col-md-12">
      <div class="panel panel-default">
        <div class="panel-heading panel-heading-compact">
          <div class="row">
            <div class="col-xs-4">
              <i class="fa fa-id-card-o fa-2x fa-fw"></i>
              <i title="Errors in form" class="fa fa-warning fa-2x fa-fw text-danger" v-show="!_.isEmpty(errors)"></i>
              <i title="Section is complete" class="fa fa-check fa-2x fa-fw text-success" v-show="_.isEmpty(errors)"></i>
            </div>
            <div class="panel-title col-xs-4">
              General Information
            </div>
            <div class="panel-actions col-xs-4">
              <a class="btn btn-info btn-xs" v-on:click="show = !show" :title="show ? 'Minimize' : 'Maximize'">
                <i class="fa fa-fw" :class="show ? 'fa-window-minimize' : 'fa-window-maximize'"></i>
              </a>
            </div>
          </div>
        </div>
        <div class="panel-body panel-body-compact">
          <div v-for="error in errors.non_field_errors" class="alert alert-danger" role="alert">{{ error }}</div>
            <div class="row">
              <div class="col-md-6 compose-help" v-show="show">
                <dl>
                  <dt>Duration of Observing Request</dt>
                  <dd>Time that will be deducted from your proposal when this request is completed.</dd>
                  <dt>Title</dt>
                  <dd>Provide a name for this observing request.</dd>
                  <dt>Proposal</dt>
                  <dd>Select the proposal for which this observation will be made.</dd>
                  <dt>Priority</dt>
                  <dd>Select whether this request should be executed immediately (i.e. within 12 min of submission).
                      <a href="https://lco.global/documentation/">
                         More information about Rapid Response mode.
                      </a>
                  </dd>
                  <dt>Ipp Factor</dt>
                  <dd>Provide an InterProposal Priority factor for this request.
                      <a target="_blank" href="https://lco.global/files/User_Documentation/the_new_priority_factor.pdf">
                         More information about IPP.
                      </a>
                  </dd>
                </dl>
              </div>
              <div :class="show ? 'col-md-6' : 'col-md-12'">
                <form class="form-horizontal">
                  <div class="row duration" v-show="show">
                    <span class="col-md-4"><strong>Total Duration</strong></span>
                    <span class="col-md-8">{{ durationDisplay }}</span>
                  </div>
                  <customfield v-model="userrequest.group_id" label="Title" field="title" v-on:input="update" :errors="errors.group_id">
                  </customfield>
                  <customselect v-model="userrequest.proposal" label="Proposal" field="proposal" v-on:input="update"
                                 :errors="errors.proposal" :options="proposalOptions">
                  </customselect>
                  <customselect v-model="userrequest.observation_type" label="Priority" field="observation_type" v-on:input="update"
                                :errors="errors.observation_type"
                                :options="[{value: 'NORMAL', text: 'Queue scheduled (default)'},
                                           {value:'TARGET_OF_OPPORTUNITY', text: 'Rapid Response'}]">
                  </customselect>
                  <customfield v-model="userrequest.ipp_value" label="Ipp Factor" field="ipp_value"
                                v-on:input="update" :errors="errors.ipp_value">
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
                       :duration_data="_.get(duration_data, ['requests', idx], {'duration': 0})">
              </request>
              <div class="request-margin"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import $ from 'jquery';
import _ from 'lodash';
import moment from 'moment';

import modal from './util/modal.vue';
import request from './request.vue';
import cadence from './cadence.vue';
import customfield from './util/customfield.vue';
import customselect from './util/customselect.vue';

export default {
  props: ['errors', 'userrequest', 'duration_data'],
  components: {request, cadence, modal, customfield, customselect},
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
    'userrequest.operator': function(){
      return this.userrequest.requests.length > 1 ? 'MANY' : 'SINGLE';
    },
    durationDisplay: function(){
      var duration =  moment.duration(this.duration_data.duration, 'seconds');
      return duration.hours() + ' hours ' + duration.minutes() + ' minutes ' + duration.seconds() + ' seconds';
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
      console.log(newRequest)
      console.log(newRequest.data_type)
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
      payload.requests = [data.request];
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
