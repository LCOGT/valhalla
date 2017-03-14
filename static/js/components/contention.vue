<template>
<div class="contention">
  <select v-model="instrument">
    <option value="1M0-SCICAM-SINISTRO">1m Sinistro</option>
    <option value="2M0-SCICAM-SPECTRAL">2m Spectral</option>
    <option value="2M0-FLOYDS-SCICAM">2m FLOYDS</option>
    <option value="0M4-SCICAM-SBIG">.4m SBIG</option>
  </select>
  <div id="plot"></div>
</div>
</template>
<script>
import vis from 'vis';
import $ from 'jquery';
import moment from 'moment';
import 'vue-style-loader!vis/dist/vis.css';
export default {
  name: 'contention',
  data: function(){
    return {
      instrument: '',
      contention: [],
      options: {
        style: 'bar',
        barChart: {align:'right'},
        moveable: false,
        stack: true,
        showMajorLabels: false,
        drawPoints: false,
        autoResize: true,
        dataAxis: {
          left: {
            range: {
              min: 0
            },
            title: {
              text: 'Total Requested Hours'
            }
          },
        },
      }
    };
  },
  computed: {
    toVis: function(){
      var items = new vis.DataSet();
      var groups = new vis.DataSet();
      for(var ra in this.contention){
        for(var prop in this.contention[ra]){
          items.add({
            group: prop,
            x: Number(ra) * 1000,
            y: this.contention[ra][prop] / 3600,
          });
          if(!groups.get(prop)){
            groups.add({
              id: prop,
              content: prop
            });
          }
        }
      }
      return {groups: groups, items: items};
    },
  },
  created: function(){
    this.instrument = '0M4-SCICAM-SBIG';
  },
  watch: {
    instrument: function(instrument){
      var that = this;
      $.getJSON('/api/contention/' + instrument + '/', function(data){
        that.contention = data;
        that.graph.setItems(new vis.DataSet());
        that.graph.setGroups(new vis.DataSet());
        that.graph.setGroups(that.toVis.groups);
        that.graph.setItems(that.toVis.items);
        that.graph.fit();
      });
    }
  },
  mounted: function(){
    this.graph = new vis.Graph2d(this.$el, this.toVis, this.groups, this.options);
  }
};
</script>
<style>
</style>
