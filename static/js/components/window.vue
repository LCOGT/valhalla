<template>
  <div class="row window" :id="'window' + $parent.index + index">
    <div class="col-md-12">
      <div class="panel panel-default">
        <div class="panel-heading panel-heading-compact">
          <div class="row">
            <div class="col-xs-4">
              <i class="fa fa-calendar fa-2x fa-fw"></i>
              <i title="Errors in form" class="fa fa-warning fa-2x fa-fw text-danger" v-show="!_.isEmpty(errors)"></i>
              <i title="Section is complete" class="fa fa-check fa-2x fa-fw text-success" v-show="_.isEmpty(errors)"></i>
            </div>
            <div class="panel-title col-xs-4">
              Window <span v-show="index > 0">#{{ index + 1}}</span>
            </div>
            <div class="panel-actions col-xs-4">
              <a class="btn btn-xs btn-danger" v-on:click="$parent.removeWindow(index)" v-show="$parent.request.windows.length > 1" title="remove">
                <i class="fa fa-trash fa-fw"></i>
              </a>
              <a class="btn btn-xs btn-success" v-on:click="$parent.addWindow(index)" title="copy"><i class="fa fa-copy fa-fw"></i></a>
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
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import {collapseMixin} from '../utils.js';
import customfield from './util/customfield.vue';
import customselect from './util/customselect.vue';
export default {
  props: ['window', 'index', 'errors', 'parentshow'],
  components: {customfield, customselect},
  mixins: [collapseMixin],
  data: function(){
    return {
      show: true,
      cadence: false,
      period: 24.0,
      jitter: 12.0
    };
  },
  computed: {
    _: function(){
      return _;
    }
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
