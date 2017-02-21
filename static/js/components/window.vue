<template>
  <panel :id="'window' + $parent.$parent.index + index" :errors="errors" v-on:show="show = $event"
         :canremove="this.index > 0" :cancopy="true" icon="fa-calendar" title="Window" v-on:remove="$emit('remove')"
         v-on:copy="$emit('copy')" :show="show">
    <div v-for="error in errors.non_field_errors" class="alert alert-danger" role="alert">{{ error }}</div>
    <div class="row">
      <div class="col-md-6 compose-help" v-show="show">
        <h4 class="text-center">Visibility</h4>
        <airmass v-show="showAirmass" :data="airmassData" :showZoomControls="true"></airmass>
      </div>
      <div :class="show ? 'col-md-6' : 'col-md-12'">
        <form class="form-horizontal" >
          <customfield v-model="window.start" type="datetime" label="Start (UT)" field="start" v-on:input="update"
                       :errors="errors.start" desc="Time when the observing window opens.">
          </customfield>
          <customfield v-model="window.end" type="datetime" label="End (UT)" field="end" v-on:input="update"
                      :errors="errors.end" desc="Time when the observing window closes.">
          </customfield>
          <customselect v-model="cadence" label="Cadence" field="cadence"
                        desc="A cadence will replace your current observing window with a set of windows, one for each cycle of the cadence."
                        :options="[{'text':'None','value':'none'}, {'text':'Simple Period',value:'simple'}]">
          </customselect>
          <customfield v-model="period" label="Period" field="period" v-on:input="update"
                       :errors="errors.period" v-show="cadence === 'simple'" desc="Fractional hours">
          </customfield>
          <customfield v-model="jitter" label="Jitter" field="jitter" v-on:input="update"
                       :errors="errors.jitter" v-show="cadence === 'simple'"
                       desc="Acceptable deviation (before or after) from strict period.">
          </customfield>
          <a class="btn btn-info col-sm-8 col-sm-offset-4" v-on:click="genCadence" v-show="cadence != 'none'">Generate Cadence</a>
        </form>
      </div>
    </div>
  </panel>
</template>
<script>
import $ from 'jquery';
import _ from 'lodash';

import {collapseMixin} from '../utils.js';
import panel from './util/panel.vue';
import customfield from './util/customfield.vue';
import customselect from './util/customselect.vue';
import airmass from './airmass.vue';

export default {
  props: ['window', 'index', 'errors', 'parentshow', 'simple_interface'],
  components: {customfield, customselect, panel, airmass},
  mixins: [collapseMixin],
  data: function(){
    return {
      show: this.parentshow,
      airmassData: {},
      showAirmass: false,
      cadence: 'none',
      period: 24.0,
      jitter: 12.0
    };
  },
  methods: {
    update: function(){
      this.$emit('windowupdate');
    },
    genCadence: function(){
      this.$emit('cadence', {
        'start': this.window.start, 'end': this.window.end, 'period': this.period, 'jitter': this.jitter
      });
    },
    updateVisibility: _.debounce(function(req){
      var request = _.cloneDeep(req);
      //replace the window list with a single window with this start/end
      request['windows'] = [{start:this.window.start, end:this.window.end}];
      var that = this;
      $.ajax({
        type: 'POST',
        url: '/api/airmass/',
        data: JSON.stringify(request),
        contentType: 'application/json',
        success: function (data) {
          that.airmassData = data;
          that.showAirmass = 'airmass_limit' in data;
        }
      });
    }, 300),
  },
};
</script>
