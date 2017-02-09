<template>
  <panel :id="'constraints' + $parent.index" :errors="errors" v-on:show="show = $event"
         :canremove="false" :cancopy="false" icon="fa-lock" title="Constraints" :show="show">
    <div v-for="error in errors.non_field_errors" class="alert alert-danger" role="alert">
      {{ error }}
    </div>
    <div class="row">
      <div class="col-md-6 compose-help" v-show="show">
      </div>
      <div :class="show ? 'col-md-6' : 'col-md-12'">
        <form class="form-horizontal">
          <customfield v-model="constraints.max_airmass" label="Maximum Airmass" field="max_airmass"
                       v-on:input="update" :errors="errors.max_airmass" desc="Airmass = 1 at zenith">
          </customfield>
          <customfield v-model="constraints.min_lunar_distance" label="Min. Lunar Separation"
                       field="min_lunar_distance" v-on:input="update" :errors="errors.min_lunar_distance"
                       desc="Minimum acceptable angular separation between the target and the moon.">
          </customfield>
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
  props: ['constraints', 'errors', 'parentshow'],
  components: {customselect, customfield, panel},
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
