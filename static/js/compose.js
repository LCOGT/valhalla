import Vue from 'vue';
import _ from 'lodash';
import $ from 'jquery';
import moment from 'moment';
import {datetimeFormat} from './utils.js';
import App from './compose.vue';
import * as main from './main.js';
import * as bootstrap from 'bootstrap3';

Vue.mixin({
  computed: {
    _: function(){
      return _;
    }
  }
});

Vue.filter('formatDate', function(value){
  if(value){
    return moment(String(value)).format(datetimeFormat);
  }
});

var vm = new Vue({
  el: '#app',
  render: function(h){
    return h(App);
  }
});

$('body').scrollspy({
  target: '.bs-docs-sidebar',
  offset: 180
});

export {vm};
