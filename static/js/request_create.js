/* globals _ $ Vue moment */

var userrequest = {
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
};

Vue.component('window',{
  props: ['istart', 'iend'],
  data: function(){
    return { start: this.istart, end: this.iend };
  },
  methods: {
    update: function(){
      this.$emit('windowupdate', this.$data);
    }
  },
  template: '#window-template'
});

Vue.component('request', {
  props: ['iwindows'],
  data: function(){
    return { windows: this.iwindows };
  },
  methods: {
    windowUpdated: function(data){
      this.windows[0] = data;
      this.$emit('requestupdate', this.$data);
    }
  },
  template: '#request-template'
});

Vue.component('userrequest', {
  props: ['irequests'],
  data: function(){
    return { requests: this.irequests };
  },
  methods: {
    requestUpdated: function(data){
      this.requests[0] = data;
      this.$emit('userrequestupdate', this.$data);
      console.log(this.requests[0].windows[0].start)
      this.$root.$data.userrequest.requests[0] = this.requests[0];
    }
  },
  template: '#userrequest-template'
});

var vm = new Vue({
  el: '#vueapp',
  data:{
    userrequest: userrequest
  },
  methods: {
    userrequestUpdated: function(data){
      console.log(data);
      this.userrequest = data;
    }
  }
});
