export var plotZoomMixin = {
  methods: {
    plotZoom: function(zoomValue){
      var range = this.plot.getWindow();
      var interval = range.end - range.start;

      this.plot.setWindow({
        start: range.start.valueOf() - interval * zoomValue,
        end:   range.end.valueOf()   + interval * zoomValue
      });
    }
  }
}