<template>
  <div class="row request" :id="'request' + index">
    <div class="col-md-12">
      <div class="panel panel-warning">
        <div class="panel-heading panel-heading-compact">
          <div class="row">
            <div class="col-xs-4">
              <i class="fa fa-wpexplorer fa-2x fa-fw"></i>
              <i title="Errors in form" class="fa fa-warning fa-2x fa-fw text-danger" v-show="!_.isEmpty(errors)"></i>
              <i title="Section is complete" class="fa fa-check fa-2x fa-fw text-success" v-show="_.isEmpty(errors)"></i>
            </div>
            <div class="panel-title col-xs-4">
              Request <span v-show="index > 0">#{{ index + 1}}</span>
            </div>
            <div class="panel-actions col-xs-4">
              <a class="btn btn-danger btn-xs" v-on:click="$parent.removeRequest(index)" v-show="$parent.userrequest.requests.length > 1" title="Delete">
                <i class="fa fa-trash fa-fw"></i>
              </a>
              <a class="btn btn-success btn-xs" title="Copy" v-on:click="$parent.addRequest(index)"><i class="fa fa-copy fa-fw"></i></a>
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
                <dt>Instrument</dt>
                <dd>Select the instrument with which this observation will be made.
                <a target="_blank" href="https://lco.global/observatory/instruments/">More information about LCO instruments</a>.</dd>
              </dl>
            </div>
            <div :class="show ? 'col-md-6' : 'col-md-12'">
              <form class="form-horizontal">
                 <customselect v-model="data_type" label="Observation Type" v-on:input="update" :errors="errors.data_type"
                                :options="[{value:'IMAGE', text: 'Image'}, {value:'SPECTRA', text:'Spectrum'}]">
                </customselect>
                <customselect v-model="instrument_name" label="Instrument" field="instrument_name"
                               :errors="errors.instrument_name" :options="availableInstrumentOptions">
                </customselect>
              </form>
            </div>
          </div>
          <target :target="request.target" v-on:targetupdate="targetUpdated" :datatype="data_type" :parentshow="show" :errors="_.get(errors, 'target', {})">
          </target>
          <div v-for="(molecule, idx) in request.molecules">
            <molecule :index="idx" :molecule="molecule" :selectedinstrument="instrument_name" :datatype="data_type" :parentshow="show"
                      v-on:moleculeupdate="moleculeUpdated" v-on:moleculefillwindow="moleculeFillWindow" :available_instruments="available_instruments"
                      :errors="_.get(errors, ['molecules', idx], {})"
                      :duration_data="_.get(duration_data, ['molecules', idx], {'duration':0})">
            </molecule>
          </div>
          <div v-for="(window, idx) in request.windows">
            <window :index="idx" :window="window" v-on:windowupdate="windowUpdated" :parentshow="show" v-on:cadence="cadence"
                    :errors="_.get(errors, ['windows', idx], {})">
            </window>
          </div>
          <constraints :constraints="request.constraints" v-on:constraintsupdate="constraintsUpdated" :parentshow="show" :errors="_.get(errors, 'constraints', {})">
          </constraints>
        </div>
      </div>
    </div>
  </div>
</template>
<script>
import _ from 'lodash';

import {collapseMixin} from '../utils.js';
import target from './target.vue';
import molecule from './molecule.vue';
import window from './window.vue';
import constraints from './constraints.vue';
import customfield from './util/customfield.vue';
import customselect from './util/customselect.vue';
export default {
  props: ['request', 'index', 'errors', 'available_instruments', 'parentshow', 'duration_data'],
  components: {target, molecule, window, constraints, customfield, customselect},
  mixins: [collapseMixin],
  data: function(){
    return {
      show: true,
      data_type: 'IMAGE',
      instrument_name: ''
    };
  },
  computed: {
    availableInstrumentOptions: function(){
      var options = [];
      for(var i in this.available_instruments){
        if(this.available_instruments[i].type === this.data_type){
          options.push({value: i, text: i});
        }
      }
      this.update();
      return _.sortBy(options, 'text').reverse();
    },
    firstAvailableInstrument: function(){
      return this.availableInstrumentOptions[0].value;
    }
  },
  watch: {
    data_type: function(){
      if(this.available_instruments[this.instrument_name].type != this.data_type){
        this.instrument_name = this.firstAvailableInstrument;
        this.update();
      }
    },
    instrument_name: function(value){
      if(value){
        this.request.location.telescope_class = this.available_instruments[value].class.toLowerCase();
      }
    },
    available_instruments: function(){
      if(!this.instrument_name){
        this.instrument_name = this.firstAvailableInstrument;
      }
    },
    'request.molecules.0.instrument_name': function(value){
      this.data_type = this.available_instruments[value].type;
      this.instrument_name = value;
    }
  },
  methods: {
    update: function(){
      this.$emit('requestupdate');
    },
    moleculeFillWindow: function(molecule_id){
      console.log('moleculefillwindow');
      if('largest_interval' in this.duration_data){
        var num_exposures = this.request.molecules[molecule_id].exposure_count;
        var molecule_duration = this.duration_data.molecules[molecule_id].duration;
        var available_time = this.duration_data.largest_interval - this.duration_data.duration + (molecule_duration*num_exposures);
        num_exposures = Math.floor(available_time / molecule_duration);
        this.request.molecules[molecule_id].exposure_count = Math.max(1, num_exposures);
        this.update();
      }
    },
    moleculeUpdated: function(){
      console.log('moleculeupdated');
      this.update();
    },
    windowUpdated: function(){
      console.log('windowUpdated');
      this.update();
    },
    targetUpdated: function(){
      console.log('targetUpdated');
      this.update();
    },
    constraintsUpdated: function(){
      console.log('constraintsUpdated');
      this.update();
    },
    addWindow: function(idx){
      var newWindow = JSON.parse(JSON.stringify(this.request.windows[idx]));
      this.request.windows.push(newWindow);
      this.update();
    },
    addMolecule: function(idx){
      var newMolecule = JSON.parse(JSON.stringify(this.request.molecules[idx]));
      this.request.molecules.push(newMolecule);
      this.update();
    },
    removeWindow: function(idx){
      this.request.windows.splice(idx, 1);
      this.update();
    },
    removeMolecule: function(idx){
      this.request.molecules.splice(idx, 1);
      this.update();
    },
    cadence: function(data){
      this.$emit('cadence', {'id': this.index, 'request':this.request, 'cadence': data});
    }
  }
};
</script>
