<template>
<div class="contention">
  <select v-model="instrument">
    <option value="1M0-SCICAM-SINISTRO">1m Sinistro</option>
    <option value="2M0-SCICAM-SPECTRAL">2m Spectral</option>
    <option value="2M0-FLOYDS-SCICAM">2m FLOYDS</option>
    <option value="0M4-SCICAM-SBIG">.4m SBIG</option>
  </select>
  <div id="plot"></div>
  {{ contention }}
</div>
</template>
<script>
import vis from 'vis';
import $ from 'jquery';
import 'vue-style-loader!vis/dist/vis.css';
export default {
  name: 'contention',
  data: function(){
    return {
      instrument: '1M0-SCICAM-SINISTRO',
      items: [],
      options: {
        style: 'bar',
        stack: true,
      }
    };
  },
  methods: {
    toVis: function(data){
      var items = [];
      for(var ra in data){
        for(var prop in data[ra]){
          items.push({
            x: Number(ra),
            group: prop,
            y: data[ra][prop]
          });
        }
      }
      return items;
    }
  },
  watch: {
    instrument: function(instrument){
      var that = this;
      $.getJSON('/api/contention/' + instrument + '/', function(data){
        that.items = that.toVis(data);
      });
    }
  },
  mounted: function(){
    this.timeline = new vis.Timeline(this.$el, this.items, this.options);
  }
};
</script>
<style>
</style>
