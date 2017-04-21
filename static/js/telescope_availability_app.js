import Vue from 'vue';
import $ from 'jquery';
import {siteCodeToName} from './utils.js';
import {observatoryCodeToNumber} from './utils.js';
import {telescopeCodeToName} from './utils.js';
import App from './telescope_availability_app.vue';

Vue.filter('readableSiteName', function(value){
  var split_string = value.split(".");
  var site = split_string[0];
  var observatory = split_string[1];
  var tel = split_string[2];

  return siteCodeToName[site] + ' ' + telescopeCodeToName[tel] + ' ' + observatoryCodeToNumber[observatory];
});

new Vue({
  el: '#telescope_availability_app',
  render: function(h){
    return h(App);
  }
});

