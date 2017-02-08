<template>
  <panel :id="'window' + $parent.index + index" :errors="errors" v-on:show="show = $event"
         :canremove="this.index > 0" :cancopy="true" icon="fa-calendar" title="Window" v-on:remove="$emit('remove')"
         v-on:copy="$emit('copy')" :show="show">
    <div v-for="error in errors.non_field_errors" class="alert alert-danger" role="alert">{{ error }}</div>
    <div class="row">
      <div class="col-md-6 compose-help" v-show="show">
        <dl>
          <dt>Start</dt>
          <dd>Time when the observing window opens.</dd>
          <dt>End</dt>
          <dd>Time when the observing window closes.</dd>
          <dt>Cadence</dt>
          <dd>Option to specify periodic observations within this window.
          <strong>This will remove all previously created windows.</strong>
          </dd>
          <dt v-show="cadence">Period</dt>
          <dd v-show="cadence">Fractional hours</dd>
          <dt v-show="cadence">Jitter</dt>
          <dd v-show="cadence">Acceptable deviation (before or after) from strict period.</dd>
        </dl>
      </div>
      <div :class="show ? 'col-md-6' : 'col-md-12'">
        <form class="form-horizontal" >
          <customfield v-model="window.start" type="datetime" label="Start (UT)" field="start" v-on:input="update" :errors="errors.start">
          </customfield>
          <customfield v-model="window.end" type="datetime" label="End (UT)" field="end" v-on:input="update" :errors="errors.end">
          </customfield>
          <div class="checkbox col-sm-8 col-sm-offset-4">
            <label>
              <input type="checkbox" v-model="cadence">Observe as a cadence
            </label>
          </div>
          <customfield v-model="period" label="Period" field="period" v-on:input="update" :errors="errors.period" v-show="cadence">
          </customfield>
          <customfield v-model="jitter" label="Jitter" field="jitter" v-on:input="update" :errors="errors.jitter" v-show="cadence">
          </customfield>
          <a class="btn btn-info col-sm-8 col-sm-offset-4" v-on:click="genCadence" v-show="cadence">Generate Cadence</a>
        </form>
      </div>
    </div>
  </panel>
</template>
<script>
import {collapseMixin} from '../utils.js';
import panel from './util/panel.vue';
import customfield from './util/customfield.vue';
import customselect from './util/customselect.vue';
export default {
  props: ['window', 'index', 'errors', 'parentshow'],
  components: {customfield, customselect, panel},
  mixins: [collapseMixin],
  data: function(){
    return {
      show: this.parentshow,
      cadence: false,
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
    }
  }
};
</script>
