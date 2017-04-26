<template>
  <telescope_availability :availabilityData="telescopeAvailabilityData"></telescope_availability>
</template>
<script>
import Vue from 'vue';
import $ from 'jquery';
import telescope_availability from './components/telescope_availability.vue';

export default {
  name: 'app',
  components: {telescope_availability,},
  data: function(){
    return {
      telescopeAvailabilityData: {},
    };
  },
  created: function(){
    var that = this;
    var endDate = new Date();
    var startDate = new Date(endDate);
    startDate.setDate(startDate.getDate() - 3);
    startDate.setHours(0);
    startDate.setMinutes(0);
    startDate.setSeconds(0);
    $.getJSON('/api/telescope_availability/?start=' + startDate.toISOString() + "&end=" + endDate.toISOString(),
      function(data){
        that.telescopeAvailabilityData = data;
    });
  }
};
</script>
