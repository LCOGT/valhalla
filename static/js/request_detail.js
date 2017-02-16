import Vue from 'vue';

import './request_row';
import App from './request_detail.vue';

new Vue({
  el: '#app',
  render: function(h){
    return h(App);
  }
});

