import Vue from 'vue';
import VueRouter from 'vue-router';
import _ from 'lodash';
import $ from 'jquery';
import {formatDate} from './utils.js';
import App from './compose.vue';

Vue.use(VueRouter);

const router = new VueRouter({
    mode: 'history',
    routes: []
});

Vue.mixin({
  computed: {
    _: function(){
      return _;
    }
  }
});

Vue.filter('formatDate', function(value){
  return formatDate(value);
});

var vm = new Vue({
  router,
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
