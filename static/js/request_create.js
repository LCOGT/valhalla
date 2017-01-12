/* globals _ $ Vue moment */

Vue.component('window',{
  props: ['istart', 'iend'],
  data: function(){
    return { start: this.istart, end: this.iend };
  },
  methods: {
    update: function(){
      console.log(this.$data);
      this.$emit('windowUpdate', this.$data);
    }
  },
  template: '#window-template'
});

Vue.component('request', {
  props: ['iwindows'],
  data: function(){
    console.log('wut')
    console.log(this.iwindows)
    return { windows: this.iwindows };
  },
  methods: {
    windowUpdated: function(data){
      this.$root.$data.requests[0].windows[0].start = data.start;
      this.$root.$data.requests[0].windows[0].end = data.end;
    }
  },
  template: '#request-template'
});

var vm = new Vue({
  el: '#vueapp',
  data:{
    proposal: undefined,
    group_id: undefined,
    operator: 'SINGLE',
    ipp_value: 1.0,
    observation_type: 'NORMAL',
    requests:[{
      data_type: '',
      instrument_name: '',
      target: {
        name: undefined,
        type: 'SIDEREAL',
        ra: undefined,
        dec: undefined,
        scheme: 'MPC_MINOR_PLANET'
      },
      molecules:[{
        type: 'EXPOSE',
        instrument_name: undefined,
        fitler: '',
        exposure_time: 30,
        exposure_count: 1,
        bin_x: 1,
        bin_y: 1,
        fill_window: false,
        acquire_mode: undefined,
        acquire_radius_arcsec: undefined,
      }],
      windows:[{
        start: moment().format('YYYY-M-D HH:mm:ss'),
        end: moment().format('YYYY-M-D HH:mm:ss')
      }],
      location:{
        telescope_class: undefined
      },
      constraints: {
        max_airmass: 2.0,
        min_lunar_distance: 30.0
      }
    }]
  }
});
