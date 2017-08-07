<template>
  <div>
    <div class="blockHistoryPlot" id="plot">
      <plot_controls v-show="showZoomControls" v-on:plotZoom="plotZoom"></plot_controls>
    </div>
    <div class="blockHistoryPlotLegend">
      <ul class="list-inline">
        <li class="SCHEDULED legend-item"></li>
        <li>Scheduled in the future</li>
        <li class="SCHEDULED-PAST legend-item"></li>
        <li>Scheduled in the past</li>
        <li class="CANCELED legend-item"></li>
        <li>Superseded by new schedule</li>
        <li class="ATTEMPTED legend-item"></li>
        <li>Currently running</li>
        <li class="FAILED legend-item"></li>
        <li>Failed</li>
        <li class="COMPLETED legend-item"></li>
        <li>Completed</li>
      </ul>
    </div>
  </div>
</template>
<script>
import vis from 'vis';
import $ from 'jquery';
import _ from 'lodash';
import 'vue-style-loader!vis/dist/vis.css';
import 'vue-style-loader!../../css/plot_style.css';
import plot_controls from './util/plot_controls.vue';
import {plotZoomMixin} from './util/plot_mixins.js';

export default {
  props: ['data', 'showZoomControls'],
  mixins: [plotZoomMixin],
  components: {plot_controls},
  data: function () {

    var options = {
      groupOrder: 'content',
      maxHeight: '450px',
      align: 'right',
      dataAttributes: ['toggle', 'html'],
      selectable: false,
      snap: null,
      zoomKey: 'ctrlKey',
      moment: function (date) {
        return vis.moment(date).utc();
      }
    };

    return {
      options: options
    };
  },
  computed: {
    toVis: function () {
      var visGroups = new vis.DataSet();
      var visData = new vis.DataSet();

      var timeline_min = 0;
      var timeline_max = 0;
      if(this.data.length > 0) {

        var previousBlock = this.data[0];
        var previousBlockIndex = 1;
        var index = 0;

        for (var i = 0; i < this.data.length; i++) {
          var block = this.data[i];
          block.start += 'Z';
          block.end += 'Z';
          var state = '';
          if (block.completed) state += ' COMPLETED';
          else if (block.failed) {
            state += ' FAILED';
            block.fail_reason = '<br/>' + block.fail_reason;
          }
          else if (block.attempted) state += ' ATTEMPTED';
          else if (block.canceled) state += ' CANCELED';
          else if (new Date(block.end) < new Date().getTime()) state += 'SCHEDULED-PAST';
          else state += 'SCHEDULED';

          block.state = state;

          if (block.cancel_date != null) {
            block.cancel_date = '<br/>canceled: ' + block.cancel_date.replace('T', ' ');
          }
          else {
            block.cancel_date = '';
          }
          if (block.start != previousBlock.start || block.site != previousBlock.site || block.state != previousBlock.state
            || block.observatory != previousBlock.observatory || block.telescope != previousBlock.telescope) {

            var className = 'timeline_block ' + previousBlock.state;

            visGroups.add({id: index, content: previousBlockIndex});

            visData.add({
              id: index,
              group: index,
              title: 'telescope: ' + previousBlock.site + '.' + previousBlock.observatory + '.' + previousBlock.telescope + previousBlock.fail_reason + previousBlock.cancel_date + '<br/>start: ' + previousBlock.start.replace('T', ' ') + '<br/>end: ' + previousBlock.end.replace('T', ' '),
              className: className,
              start: previousBlock.start,
              end: previousBlock.end,
              toggle: 'tooltip',
              html: true,
              type: 'range'
            });
            index++;
            previousBlockIndex = i + 1;
          }
          previousBlock = block;
        }

        visGroups.add({id: index, content: previousBlockIndex});

        visData.add({
          id: index,
          group: index,
          title: 'telescope: ' + previousBlock.site + '.' + previousBlock.observatory + '.' + previousBlock.telescope + previousBlock.fail_reason + previousBlock.cancel_date + '<br/>start: ' + previousBlock.start.replace('T', ' ') + '<br/>end: ' + previousBlock.end.replace('T', ' '),
          className: 'timeline_block ' + previousBlock.state,
          start: previousBlock.start,
          end: previousBlock.end,
          toggle: 'tooltip',
          html: true,
          type: 'range'
        });
        index++;

        timeline_min = new Date(visData.get(index - 1)['start']);
        timeline_max = new Date(visData.get(index - 1)['end']);
        if (index > 12) {
          for (var k = index - 1; k >= index - 12; k--) {
            var start = new Date(visData.get(k)['start']);
            var end = new Date(visData.get(k)['end']);
            if (start < timeline_min) {
              timeline_min = start;
            }
            if (end > timeline_max) {
              timeline_max = end;
            }
          }
          timeline_max.setMinutes(timeline_max.getMinutes() + 30);
          timeline_min.setMinutes(timeline_min.getMinutes() - 30);
        }
      }

      return {datasets: visData, groups: visGroups, window: {start: timeline_min, end: timeline_max}};
    }
  },
  watch: {
    data: function () {
      var datasets = this.toVis;
      //Need to first zero out the items and groups or vis.js throws an error
      this.plot.setItems(new vis.DataSet());
      this.plot.setGroups(new vis.DataSet());
      this.plot.setGroups(datasets.groups);
      this.plot.setItems(datasets.datasets);
      this.plot.setWindow(datasets.window.start, datasets.window.end);
    }
  },
  mounted: function () {
    this.plot = this.buildPlot();
  },
  methods: {
    buildPlot: function () {
      // Set a unique name for the plot element, since vis.js needs this to separate plots
      this.$el.setAttribute('class', _.uniqueId(this.$el.className));
      var plot = new vis.Timeline(document.getElementById('plot'), new vis.DataSet([]), this.options);
      var that = this;
      plot.on('changed', function () {
        //HAX
        $(that.$el).find('.vis-group').mouseover(function () {
          $(that.$el).find('.vis-item').tooltip({container: 'body'});
        });
      });
      return plot;
    }
  }
};
</script>
<style>
.blockHistoryPlotLegend ul {
  text-align: center;
}
</style>
