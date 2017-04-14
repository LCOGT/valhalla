<template>
<div class="pressure">
  <label for="pressure-instrument">Instrument</label>
  <select id="pressure-instrument" v-model="instrument">
    <option value="">All</option>
    <option value="1M0-SCICAM-SINISTRO">1m Sinistro</option>
    <option value="2M0-SCICAM-SPECTRAL">2m Spectral</option>
    <option value="2M0-FLOYDS-SCICAM">2m FLOYDS</option>
    <option value="0M4-SCICAM-SBIG">.4m SBIG</option>
  </select>
  <label for="pressure-site">Site</label>
  <select id="pressure-site" v-model="site">
    <option value="">All</option>
    <option value="coj">Siding Spring (coj)</option>
    <option value="cpt">Sutherlan, South Africa (cpt)</option>
    <option value="elp">McDonald, Texas (elp)</option>
    <option value="lsc">Cerro Tololo, Chile (lsc)</option>
    <option value="ogg">Maui, Hawaii (ogg)</option>
    <option value="sqa">Sedgwick Reserve (sqa)</option>
    <option value="tfn">Tenerife, Canary Islands (tfn)</option>
  </select>
  <i class="fa fa-spin fa-spinner load-spinner" v-show="rawData.length < 1"></i>
  <canvas id="pressureplot" width="400" height="200"></canvas>
</div>
</template>
<script>
import Chart from 'chart.js';
import $ from 'jquery';
import {colorPalette} from '../utils.js';
import 'chartjs-plugin-annotation';

export default {
  name: 'pressure',
  data: function(){
    return {
      instrument: '',
      site: '',
      rawData: [],
      data: {
        datasets: [],
        labels: Array.apply(null, {length: 24 * 4}).map(Number.call, Number).map(function(x){ return (x / 4).toString(); })
      }
    };
  },
  computed: {
    toChartData: function(){
      var datasets = {};
      for (var time = 0; time < this.rawData.length; time++) {
        for(var proposal in this.rawData[time]){
          if(!datasets.hasOwnProperty(proposal)){
            datasets[proposal] = Array.apply(null, Array(24 * 4)).map(Number.prototype.valueOf, 0);  // fills array with 0s
          }
          datasets[proposal][time] = this.rawData[time][proposal];
        }
      }
      var grouped = [];
      var color = 0;
      for(var prop in datasets){
        grouped.push({label: prop, data: datasets[prop], backgroundColor: colorPalette[color], type: 'bar'});
        color++;
      }
      return grouped;
    }
  },
  created: function(){
    this.fetchData();
  },
  methods: {
    fetchData: function(){
      this.rawData = [];
      var urlstring = '/api/pressure/?x=0';
      if(this.site) urlstring += ('&site=' + this.site);
      if(this.instrument) urlstring += ('&instrument=' + this.instrument);
      var that = this;
      $.getJSON(urlstring, function(data){
        that.rawData = data;
        that.data.datasets = that.toChartData;
        that.chart.update();
      });
    }
  },
  watch: {
    instrument: function(){
      this.fetchData();
    },
    site: function(){
      this.fetchData();
    }
  },
  mounted: function(){
    var that = this;
    var ctx = document.getElementById('pressureplot');
    this.chart = new Chart(ctx, {
      type: 'bar',
      data: that.data,
      options: {
        annotation: {
          annotations: [{
            type: 'line',
            mode: 'horizontal',
            scaleID: 'y-axis-0',
            value: '1.0',
            borderColor: 'black',
            borderDash: [5, 8],
            borderWidth: 4,
          }]
        },
        scales:{
          xAxes: [{
            stacked: true,
            scaleLabel: {
              display: true,
              labelString: 'Hours From Now'
            },
            ticks: {
              maxTicksLimit: 25
            }
          }],
          yAxes: [{
            stacked: true,
            scaleLabel: {
              display: true,
              labelString: 'Pressure'
            }
          }]
        },
        tooltips: {
          callbacks: {
            label: function(tooltipItem){
              return that.data.datasets[tooltipItem.datasetIndex].label + ' ' +tooltipItem.yLabel.toFixed(3);
            }
          }
        }
      }
    });
  }
};
</script>
