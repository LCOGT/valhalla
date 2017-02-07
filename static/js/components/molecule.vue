<template>
  <div class="row target" :id="'molecule' + $parent.index + index">
    <div class="col-md-12">
      <div class="panel panel-default">
        <div class="panel-heading panel-heading-compact">
          <div class="row">
            <div class="col-xs-4">
              <i class="fa fa-cogs fa-2x fa-fw"></i>
              <i title="Errors in form" class="fa fa-warning fa-2x fa-fw text-danger" v-show="!_.isEmpty(errors)"></i>
              <i title="Section is complete" class="fa fa-check fa-2x fa-fw text-success" v-show="_.isEmpty(errors)"></i>
            </div>
            <div class="panel-title col-xs-4">
              Configuration <span v-show="index > 0">#{{ index + 1 }}</span>
            </div>
            <div class="panel-actions col-xs-4">
              <a class="btn btn-danger btn-xs" v-on:click="$parent.removeMolecule(index)" v-show="$parent.request.molecules.length > 1" title="Remove">
                <i class="fa fa-trash fa-fw"></i>
              </a>
              <a class="btn btn-success btn-xs" v-on:click="$parent.addMolecule(index)" title="Copy"><i class="fa fa-copy fa-fw"></i></a>
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
                <dt>Filter/Slit</dt>
                <dd>The filter to be used if used with an imaging instrument, or slit to be used with a spectrograph.</dd>
                <dt>Binning</dt>
                <dd>Number of CCD pixels in X and Y to bin together. The recommended binning will be selected by default.</dd>
                <dt>Exposure Count</dt>
                <dd>Number of exposures to make with this configuration.</dd>
                <dt>Exposure Time</dt>
                <dd>Seconds</dd>
              </dl>
              <dl v-show="datatype === 'SPECTRA'">
                <dt>Type</dt>
                <dd>The type of exposure (allows for calibrations).</dd>
                <dt>Acquire Mode</dt>
                <dd>How the target is acquired.</dd>
              </dl>
            </div>
            <div :class="show ? 'col-md-6' : 'col-md-12'">
              <form class="form-horizontal">
                <customselect v-model="molecule.filter" :label="datatype === 'IMAGE' ? 'Filter':'Slit Width'" v-on:input="update"
                               :errors="errors.filter" :options="filterOptions">
                </customselect>
                <customselect v-model="molecule.bin_x" label="Binning" v-on:input="binningsUpdated"
                               :errors="errors.bin_x" :options="binningsOptions">
                </customselect>
                <customfield v-model="molecule.exposure_count" label="Exposure Count" field="exposure_count" v-on:input="update"
                                :errors="errors.exposure_count">
                  <div class="input-group-btn" slot="inlineButton">
                    <button class="btn btn-default" type="button" style="font-size:16px" v-on:click="fillWindow"
                            :disabled="duration_data.duration > 0 ? false : true"><b>Fill</b></button>
                  </div>
                </customfield>
                <customfield v-model="molecule.exposure_time" label="Exposure Time" field="exposure_time" v-on:input="update"
                              :errors="errors.exposure_time">
                </customfield>
                <div class="spectra" v-if="datatype === 'SPECTRA'">
                  <customselect v-model="molecule.type" label="Type" v-on:input="update" :errors="errors.type"
                                 :options="[{value: 'SPECTRUM', text: 'Spectrum'},
                                            {value: 'LAMP_FLAT', text: 'Lamp Flat'},
                                            {value: 'ARC', text:'Arc'}]">
                  </customselect>
                  <customselect v-model="molecule.acquire_mode" label="Acquire Mode" v-on:input="update" :errors="errors.acquire_mode"
                                 :options="[{value: 'OFF', text: 'Off'},
                                            {value: 'WCS', text: 'WCS'},
                                            {value: 'BRIGHTEST', text: 'Brightest'}]">
                  </customselect>
                  <customfield v-show="molecule.acquire_mode === 'BRIGHTEST'" v-model="molecule.acquire_radius_arcsec" field="acquire_radius_arcsec"
                                label="Acquire Radius" v-on:input="update" :errors="errors.acquire_radius_arcsec">
                  </customfield>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import _ from 'lodash';

import {collapseMixin} from '../utils.js';
import customfield from './util/customfield.vue';
import customselect from './util/customselect.vue';
export default {
  props: ['molecule', 'index', 'errors', 'selectedinstrument', 'available_instruments', 'datatype', 'parentshow', 'duration_data'],
  components: {customfield, customselect},
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
