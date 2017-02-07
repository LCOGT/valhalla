<template>
  <div class="row constraints" :id="'constraints' + $parent.index">
    <div class="col-md-12">
      <div class="panel panel-default">
        <div class="panel-heading panel-heading-compact">
          <div class="row">
            <div class="col-xs-4">
              <i class="fa fa-lock fa-2x fa-fw"></i>
              <i title="Errors" class="fa fa-warning fa-2x fa-fw text-danger" v-show="!_.isEmpty(errors)"></i>
              <i title="Complete" class="fa fa-check fa-2x fa-fw text-success" v-show="_.isEmpty(errors)"></i>
            </div>
            <div class="panel-title col-xs-4">
              Constraints
            </div>
            <div class="panel-actions col-xs-4">
              <a class="btn btn-info btn-xs" v-on:click="show = !show"
                 :title="show ? 'Minimize' : 'Maximize'">
                <i class="fa fa-fw" :class="show ? 'fa-window-minimize' : 'fa-window-maximize'"></i>
              </a>
            </div>
          </div>
        </div>
        <div class="panel-body panel-body-compact">
          <div v-for="error in errors.non_field_errors" class="alert alert-danger" role="alert">
            {{ error }}
          </div>
          <div class="row">
            <div class="col-md-6 compose-help" v-show="show">
              <dl>
                <dt>Maximum Airmass</dt>
                <dd>Airmass = 1 at zenith.</dd>
                <dt>Minimum Lunar Separation</dt>
                <dd>Minimum acceptable angular separation between the target and the moon.</dd>
              </dl>
            </div>
            <div :class="show ? 'col-md-6' : 'col-md-12'">
              <form class="form-horizontal">
                <customfield v-model="constraints.max_airmass" label="Maximum Airmass" field="max_airmass"
                              v-on:input="update" :errors="errors.max_airmass">
                </customfield>
                <customfield v-model="constraints.min_lunar_distance" label="Min. Lunar Distance"
                              field="min_lunar_distance" v-on:input="update"
                              :errors="errors.min_lunar_distance">
                </customfield>
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
  props: ['constraints', 'errors', 'parentshow'],
  components: {customselect, customfield},
  mixins: [collapseMixin],
  data: function(){
    return {'show': true};
  },
  methods: {
    update: function(){
      this.$emit('constraintsupdate');
    }
  }
};
</script>
