<template>
  <panel :id="'molecule' + $parent.$parent.index + index" :errors="errors" v-on:show="show = $event"
         :canremove="this.index > 0" :cancopy="true" icon="fa-cogs" title="Configuration" v-on:remove="$emit('remove')"
         v-on:copy="$emit('copy')" :show="show">
    <div v-for="error in errors.non_field_errors" class="alert alert-danger" role="alert">{{ error }}</div>
    <div class="row">
      <div class="col-md-6 compose-help" v-show="show">
        <ul>
          <li>
            Try the
            <a href="https://lco.global/files/etc/exposure_time_calculator.html">
              online exposure time calculator.
            </a>
          </li>
        </ul>
        <div class="row" v-show="molecule.type === 'SPECTRUM'">
          <div class="col-md-12">
            <h2>Automatic generation of calibration frames</h2>
            <p>
              Since you are taking a spetrum, it is recommended you also schedule calibrations for before
              and after your exposure.
            </p>
            <a class="btn btn-default" v-on:click="generateCalibs" v-show="molecule.type === 'SPECTRUM'">Create calibration frames</a>
          </div>
        </div>
      </div>
      <div :class="show ? 'col-md-6' : 'col-md-12'">
        <form class="form-horizontal">
          <customselect v-model="molecule.filter" :label="datatype === 'IMAGE' ? 'Filter':'Slit Width'" v-on:input="update"
                         :errors="errors.filter" :options="filterOptions"
                         desc="The filter to be used if used with an imaging instrument, or slit to be used with a spectrograph.">
          </customselect>
          <customselect v-model="molecule.bin_x" label="Binning" v-on:input="binningsUpdated"
                         :errors="errors.bin_x" :options="binningsOptions"
                         desc="Number of CCD pixels in X and Y to bin together. The recommended binning will be selected by default.">
          </customselect>
          <customfield v-model="molecule.exposure_count" label="Exposure Count" field="exposure_count" v-on:input="update"
                       :errors="errors.exposure_count" desc="Number of exposures to make with this configuration.">
            <div class="input-group-btn" slot="inlineButton">
              <button class="btn btn-default" type="button" style="font-size:16px" v-on:click="fillWindow"
                      :disabled="duration_data.duration > 0 ? false : true"><b>Fill</b></button>
            </div>
          </customfield>
          <customfield v-model="molecule.exposure_time" label="Exposure Time" field="exposure_time" v-on:input="update"
                       :errors="errors.exposure_time" desc="Seconds">
          </customfield>
          <customfield v-model="molecule.defocus" label="Defocus" field="defocus" v-on:input="update"
                       :errors="errors.defocus">
          </customfield>
          <customselect v-model="molecule.ag_mode" label="Guiding" field="ag_mode" v-on:input="update"
                        :errors="errors.ag_mode" desc="Whether or not to force autoguiding."
                        :options="[{value: 'OPTIONAL', text: 'Optional'},
                                   {value: 'OFF', text: 'Off'},
                                   {value: 'ON', text: 'On'}]">
          </customselect>
          <div class="spectra" v-if="datatype === 'SPECTRA'">
            <customselect v-model="molecule.type" label="Type" v-on:input="update" :errors="errors.type"
                          desc="The type of exposure (allows for calibrations)."
                          :options="[{value: 'SPECTRUM', text: 'Spectrum'},
                                      {value: 'LAMP_FLAT', text: 'Lamp Flat'},
                                      {value: 'ARC', text:'Arc'}]">
            </customselect>
            <customselect v-model="molecule.acquire_mode" label="Acquire Mode" v-on:input="update" :errors="errors.acquire_mode"
                          desc="How the target is acquired."
                          :options="[{value: 'OFF', text: 'Off'},
                                     {value: 'WCS', text: 'WCS'},
                                     {value: 'BRIGHTEST', text: 'Brightest'}]">
            </customselect>
            <customfield v-show="molecule.acquire_mode === 'BRIGHTEST'" v-model="molecule.acquire_radius_arcsec" field="acquire_radius_arcsec"
                         label="Acquire Radius" v-on:input="update" :errors="errors.acquire_radius_arcsec" desc="Arc seconds">
            </customfield>
          </div>
        </form>
      </div>
    </div>
  </panel>
</template>
<script>
import _ from 'lodash';

import {collapseMixin} from '../utils.js';
import panel from './util/panel.vue';
import customfield from './util/customfield.vue';
import customselect from './util/customselect.vue';
export default {
  props: ['molecule', 'index', 'errors', 'selectedinstrument', 'available_instruments', 'datatype', 'parentshow', 'duration_data'],
  components: {customfield, customselect, panel},
  mixins: [collapseMixin],
  data: function(){
    return {
      show: true,
      acquire_params: {
        acquire_mode: 'OFF',
        acquire_radius_arcsec: null
      }
    };
  },
  computed: {
    filterOptions: function(){
      var options = [{value: '', text: ''}];
      var filters = _.get(this.available_instruments, [this.selectedinstrument, 'filters'], []);
      for(var filter in filters){
        if(['Standard', 'Slit', 'VirtualSlit'].indexOf(filters[filter].type) > -1){ // TODO select on mode
          options.push({value: filter, text: filters[filter].name});
        }
      }
      return _.sortBy(options, 'text');
    },
    binningsOptions: function(){
      var options = [];
      var binnings = _.get(this.available_instruments, [this.selectedinstrument, 'binnings'], []);
      binnings.forEach(function(binning){
        options.push({value: binning, text: binning});
      });
      return options;
    },
  },
  methods: {
    update: function(){
      this.$emit('moleculeupdate');
    },
    binningsUpdated: function(){
      this.molecule.bin_y = this.molecule.bin_x;
      this.update();
    },
    fillWindow: function(){
      console.log('fillWindow');
      this.$emit('moleculefillwindow', this.index);
    },
    generateCalibs: function(){
      this.$emit('generateCalibs', this.index)
    }
  },
  watch: {
    selectedinstrument: function(value){
      if(this.molecule.instrument_name != value){
        this.molecule.instrument_name = value;
        this.molecule.filter = '';
        // wait for options to update, then set default
        var that = this;
        setTimeout(function(){
          var default_binning = _.get(
            that.available_instruments, [that.selectedinstrument, 'default_binning'], null
          );
          that.molecule.bin_x = default_binning;
          that.molecule.bin_y = default_binning;
          that.update();
        }, 100);
      }
    },
    datatype: function(value){
      this.molecule.type = (value === 'IMAGE') ? 'EXPOSE': 'SPECTRUM';
      if (value === 'SPECTRA'){
        this.molecule.acquire_mode = this.acquire_params.acquire_mode;
        if (this.molecule.acquire_mode === 'BRIGHTEST'){
          this.molecule.acquire_radius_arcsec = this.acquire_params.acquire_radius_arcsec;
        }
      }
      else{
        this.acquire_params.acquire_mode = this.molecule.acquire_mode;
        this.molecule.acquire_mode = undefined;
        this.molecule.acquire_radius_arcsec = undefined;
      }
    },
    'molecule.acquire_mode': function(value){
      if(value === 'BRIGHTEST'){
        this.molecule.acquire_radius_arcsec = this.acquire_params.acquire_radius_arcsec;
      }
      else{
        if(typeof this.molecule.acquire_radius_arcsec != undefined){
          this.acquire_params.acquire_radius_arcsec = this.molecule.acquire_radius_arcsec;
          this.molecule.acquire_radius_arcsec = undefined;
        }
      }
    }
  }
};
</script>
