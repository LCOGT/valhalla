<template>
  <telescope_availability :availabilityData="availabilityData2"></telescope_availability>
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
      availabilityData2: {},
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
        that.availabilityData2 = data;
    });
  }
};
</script>
