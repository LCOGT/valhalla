<template>
  <div class="row target" :id="'target' + $parent.index">
    <div class="col-md-12">
      <div class="panel panel-default">
        <div class="panel-heading panel-heading-compact">
          <div class="row">
            <div class="col-xs-4">
              <i class="fa fa-crosshairs fa-2x fa-fw"></i>
              <i title="Errors in form" class="fa fa-warning fa-2x fa-fw text-danger" v-show="!_.isEmpty(errors)"></i>
              <i title="Section is complete" class="fa fa-check fa-2x fa-fw text-success" v-show="_.isEmpty(errors)"></i>
            </div>
            <div class="panel-title col-xs-4">
              Target
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
                <dt>Type</dt>
                <dd>Please select whether this is a <strong>sidereal</strong> or <strong>non-sidereal</strong> target.</dd>
              </dl>
              <dl v-show="target.type === 'SIDEREAL'">
                <dt>Right Ascension</dt>
                <dd>Decimal degrees or HH:MM:SS.S</dd>
                <dt>Declination</dt>
                <dd>Decimal degrees of DD:MM:SS.S</dd>
                <dt>Proper Motion RA</dt>
                <dd>&plusmn;0.33 mas/year</dd>
                <dt>Proper Motion Dec</dt>
                <dd>&plusmn;0.33 mas/year</dd>
                <dt>Epoch</dt>
                <dd>Julian Years</dd>
                <dt>Parallax</dt>
                <dd>+0.45 mas</dd>
              </dl>
              <dl v-show="target.type === 'NON_SIDEREAL'">
                <dt>Scheme</dt>
                <dd>The orbital elements scheme to use with this target</dd>
                <dt>Epoch</dt>
                <dd>Modified Julian Days</dd>
                <dt>Longitude of Ascending Node</dt>
                <dd>Andle in Degrees</dd>
                <dt>Argument of Perihelion</dt>
                <dd>Angle in Degrees</dd>
                <dt>Mean Distance</dt>
                <dd>Astronomical Units</dd>
                <dt>Eccentricity</dt>
                <dd>0 to 0.99</dd>
                <dt>Mean Anomaly</dt>
                <dd>fAngle in Degrees</dd>
              </dl>
            </div>
            <div :class="show ? 'col-md-6' : 'col-md-12'">
              <form class="form-horizontal">
                <customfield v-model="target.name" label="Target Name" field="name" v-on:input="update" :errors="errors.name">
                </customfield>
                <div class="row" v-show="lookingUP">
                    <span class="col-md-12" style="text-align: right">
                      <i class="fa fa-spinner fa-spin fa-fw"></i> Looking up coordinates...
                    </span>
                </div>
                <customselect v-model="target.type" label="Type" field="type" v-on:input="update" :errors="errors.type"
                               :options="[{value: 'SIDEREAL',text: 'Sidereal'}, {value: 'NON_SIDEREAL',text:'Non-Sidereal'}]">
                </customselect>
                <div class="sidereal" v-if="target.type === 'SIDEREAL'">
                  <customfield v-model="target.ra" label="Right Ascension" type="sex" field="ra" v-on:blur="updateRA" :errors="errors.ra">
                  </customfield>
                  <customfield v-model="target.dec" label="Declination" type="sex" field="dec" v-on:blur="updateDec" :errors="errors.dec">
                  </customfield>
                  <customfield v-model="target.proper_motion_ra" label="Proper Motion: RA" field="proper_motion_ra"
                                v-on:input="update" :errors="errors.proper_motion_ra">
                  </customfield>
                  <customfield v-model="target.proper_motion_dec" label="Proper Motion: Dec" field="proper_motion_dec"
                                v-on:input="update" :errors="errors.proper_motion_dec">
                  </customfield>
                  <customfield v-model="target.epoch" label="Epoch" field="epoch" v-on:input="update" :errors="errors.epoch">
                  </customfield>
                  <customfield v-model="target.parallax" label="Parallax" field="parallax" v-on:input="update"
                                :errors="errors.parallax">
                  </customfield>
                </div>
                <div class="non-sidereal" v-if="target.type === 'NON_SIDEREAL'">
                  <customselect v-model="target.scheme" label="Scheme" field="scheme" v-on:input="update" :errors="errors.scheme"
                                 :options="[{value: 'MPC_MINOR_PLANET', text: 'MPC Minor Planet'},
                                            {value: 'MPC_COMET', text: 'MPC Comet'}]">
                  </customselect>
                  <customfield v-model="target.epoch" label="Epoch" field="epoch" v-on:input="update" :errors="errors.epoch">
                  </customfield>
                  <customfield v-model="target.orbinc" label="Orbital Inclination" field="orbinc" v-on:input="update"
                                :errors="errors.orbinc">
                  </customfield>
                  <customfield v-model="target.longascnode" label="Longitude of Ascending Node" field="longascnode"
                                v-on:input="update" :errors="errors.longascnode">
                  </customfield>
                  <customfield v-model="target.argofperih" label="Argument of Perihelion" field="argofperih"
                                v-on:input="update" :errors="errors.argofperih">
                  </customfield>
                  <customfield v-model="target.meandist" label="Mean Distance (AU)" field="meandist"
                                v-on:input="update" :errors="errors.meandist">
                  </customfield>
                  <customfield v-model="target.eccentricity" label="Eccentricity" field="eccentricity"
                                v-on:input="update" :errors="errors.eccentricity">
                  </customfield>
                  <customfield v-model="target.meananom" label="Mean Anomoly" field="meananom"
                                v-on:input="update" :errors="errors.meananom">
                  </customfield>
                </div>
                <div class="spectra" v-if="datatype === 'SPECTRA'">
                  <customselect v-model="target.rot_mode" label="Rotator Mode" field="rot_mode" v-on:input="update" :errors="errors.rot_mode"
                                 :options="[{value: 'SKY', text: 'Sky'}, {value: 'VFLOAT', text: 'Vertical Floating'}]">
                  </customselect>
                  <customfield v-model="target.rot_angle" label="Rotator Angle" field="rot_angle" v-on:input="update" :errors="errors.rot_angle">
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
import $ from 'jquery';

import {collapseMixin, sexagesimalRaToDecimal, sexagesimalDecToDecimal} from '../utils.js';
import customfield from './util/customfield.vue';
import customselect from './util/customselect.vue';
export default {
  props: ['target', 'errors', 'datatype', 'parentshow'],
  components: {customfield, customselect},
  mixins: [collapseMixin],
  data: function(){
    var ns_target_params = {
      scheme: 'MPC_MINOR_PLANET',
      orbinc: 0,
      longascnode: 0,
      argofperih: 0,
      meandist: 0,
      eccentricity: 0,
      meananom: 0
    };
    var rot_target_params = {rot_mode: 'SKY', rot_angle: 0};
    var sid_target_params = _.cloneDeep(this.target);
    delete sid_target_params['name'];
    delete sid_target_params['epoch'];
    delete sid_target_params['type'];
    return {show: true, lookingUP: false, ns_target_params: ns_target_params, sid_target_params: sid_target_params, rot_target_params: rot_target_params};
  },
  methods: {
    update: function(){
      this.$emit('targetupdate', {});
    },
    updateRA: function(){
      this.ra = sexagesimalRaToDecimal(this.ra);
      this.update();
    },
    updateDec: function(){
      this.dec = sexagesimalDecToDecimal(this.dec);
      this.update();
    }
  },
  watch: {
    'target.name': _.debounce(function(name){
      this.lookingUP = true;
      var that = this;
      $.getJSON('https://lco.global/lookUP/json/?name=' + name).done(function(data){
        that.target.ra = _.get(data, ['ra', 'decimal'], null);
        that.target.dec = _.get(data, ['dec', 'decimal'], null);
        that.target.proper_motion_ra = data.pmra;
        that.target.proper_motion_dec = data.pmdec;
        that.update();
      }).always(function(){
        that.lookingUP = false;
      });
    }, 500),
    'datatype': function(value){
      if(value === 'SPECTRA'){
        for(var x in this.rot_target_params){
          this.target[x] = this.rot_target_params[x];
        }
      }else{
        for(var y in this.rot_target_params){
          this.rot_target_params[y] = this.target[y];
          this.target[y] = undefined;
        }
      }
    },
    'target.type': function(value){
      var that = this;
      if(this.target.type === 'SIDEREAL'){
        for(var x in this.ns_target_params){
          that.ns_target_params[x] = that.target[x];
          that.target[x] = undefined;
        }
        for(var y in this.sid_target_params){
          that.target[y] = that.sid_target_params[y];
        }
      }else if(value === 'NON_SIDEREAL'){
        for(var z in this.sid_target_params){
          that.sid_target_params[z] = that.target[z];
          that.target[z] = undefined;
        }
        for(var a in this.ns_target_params){
          that.target[a] = that.ns_target_params[a];
        }
      }
    }
  },
};
</script>
