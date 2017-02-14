<template>
  <div v-show="resultCount > 0">
    <h3>
      <i class="fa fa-fw fa-info fa-2x fa-border fa-pull-left"></i>
      <a :href="guiLink" target="_blank">
        {{ resultCount }}
      </a>
      existing frames have been found on the LCO science archive covering this RA/Dec.
    </h3>
  </div>
</template>
<script>
import $ from 'jquery';
import _ from 'lodash';
import {login, ajaxSetup} from '../archive.js';
export default {
  props: ['ra', 'dec'],
  data: function(){
    return{resultCount: 0};
  },
  created: function(){
    ajaxSetup();
    this.setResultCount();
  },
  computed: {
    guiLink: function(){
      return 'https://archive.lco.global/?start=2014-05-01&covers=POINT(' + this.ra + ' ' + this.dec +')';
    }
  },
  methods:{
    setResultCount: _.debounce(function(){
      var that = this;
      login(function(){
        $.getJSON('https://archive-api.lco.global/frames/?covers=POINT(' + that.ra + ' ' + that.dec +')', function(data){
          that.resultCount = data.count;
        });
      });
    }, 500)
  },
  watch: {
    ra: function(val){
      if(val && this.dec){
        this.setResultCount();
      }
    },
    dec: function(val){
      if(val && this.ra){
        this.setResultCount();
      }
    }
  }
};
</script>
