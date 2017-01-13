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

Vue.component('custom-field', {
  props: ['value', 'label', 'field', 'errors'],
  methods: {
    update: function(value){
      this.$emit('input', value);
    }
  },
  template: '#custom-field'
});

Vue.component('window',{
  props: ['istart', 'iend', 'index'],
  data: function(){
    return {
      start: this.istart,
      end: this.iend,
      errors: []
    };
  },
  methods: {
    update: function(){
      this.$emit('windowupdate', {'id': this.index, 'data': this.$data});
    },
    validate: function(data){
      var reqIndex = this.$parent.$data.index;
      this.errors = _.get(data, ['requests', reqIndex, 'windows', this.index], []);
    }
  },
  created: function(){
    eventHub.$on('validate', this.validate);
  },
  template: '#window-template'
});

Vue.component('request', {
  props: ['iwindows', 'idx'],
  data: function(){
    return { windows: this.iwindows, index: this.idx };
  },
  methods: {
    windowUpdated: function(data){
      Vue.set(this.windows, data.id, data.data);
      console.log('windowUpdated')
      this.$emit('requestupdate', {'id': this.index, 'data': this.$data});
    },
    addWindow: function(){
      var newWindow = {'start': moment().format('YYYY-M-D HH:mm:ss'), 'end': moment().format('YYYY-M-D HH:mm:ss')};
      this.windows.push(newWindow);
    }
  },
  template: '#request-template'
});

Vue.component('userrequest', {
  props: ['irequests', 'igroup_id', 'iproposal', 'iobservation_type'],
  data: function(){
    return {
      requests: this.irequests,
      group_id: this.igroup_id,
      proposal: this.iproposal,
      observation_type: this.iobservation_type,
      errors: []
    };
  },
  methods: {
    validate: function(data){
      this.errors = data;
    },
    update: function(){
      this.$emit('userrequestupdate', this.$data);
    },
    requestUpdated: function(data){
      console.log('request updated')
      Vue.set(this.requests, data.id, data.data);
      this.$emit('userrequestupdate', this.$data);
    },
    addRequest: function(){
      var newRequest = JSON.parse(JSON.stringify(this.requests[0]));
      this.requests.push(newRequest);
    },
  },
  created: function(){
    eventHub.$on('validate', this.validate);
  },
  template: '#userrequest-template'
});

var eventHub = new Vue();

var vm = new Vue({
  el: '#vueapp',
  data:{
    userrequest: userrequest
  },
  methods: {
    validate: function(){
      var that = this;
      $.ajax({
        type: 'POST',
        url: '/api/user_requests/validate/',
        data: JSON.stringify(that.userrequest),
        contentType: 'application/json',
        success: function(data){
          eventHub.$emit('validate', data.errors);
        }
      });
    },
    userrequestUpdated: function(data){
      console.log('userrequest updated')
      this.userrequest = data;
      this.validate();
    }
  }
});
