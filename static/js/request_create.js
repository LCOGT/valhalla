/* globals _ $ Vue moment */

Vue.component('userrequest', {
  props: ['errors'],
  data: function(){
    return {
      group_id: '',
      proposal: '',
      operator: 'SINGLE',
      ipp_value: 1,
      observation_type: 'NORMAL',
      requests: [{
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
  },
  methods: {
    update: function(){
      this.$emit('userrequestupdate', this.$data);
    },
    requestUpdated: function(data){
      console.log('request updated')
      Vue.set(this.requests, data.id, data.data);
      this.$emit('userrequestupdate', this.$data);
    },
    addRequest: function(idx){
      var newRequest = JSON.parse(JSON.stringify(this.requests[idx]));
      this.requests.push(newRequest);
    },
  },
  template: '#userrequest-template'
});

Vue.component('request', {
  props: ['irequest', 'index', 'errors'],
  data: function(){
    return this.irequest;
  },
  methods: {
    windowUpdated: function(data){
      Vue.set(this.windows, data.id, data.data);
      console.log('windowUpdated')
      this.$emit('requestupdate', {'id': this.index, 'data': this.$data});
    },
    addWindow: function(idx){
      var newWindow = JSON.parse(JSON.stringify(this.windows[idx]));
      this.windows.push(newWindow);
    }
  },
  template: '#request-template'
});

Vue.component('window',{
  props: ['iwindow', 'index', 'errors'],
  data: function(){
    return this.iwindow;
  },
  computed: {
    toRep: function(){
      return {'start': this.start, 'end': this.end};
    }
  },
  methods: {
    update: function(){
      this.$emit('windowupdate', {'id': this.index, 'data': this.toRep});
    }
  },
  template: '#window-template'
});

Vue.component('custom-field', {
  props: ['value', 'label', 'field', 'errors'],
  methods: {
    update: function(value){
      this.$emit('input', value);
    }
  },
  template: '#custom-field'
});

Vue.component('custom-select', {
  props: ['value', 'label', 'field', 'options', 'errors'],
  methods: {
    update: function(value){
      this.$emit('input', value);
    }
  },
  template: '#custom-select'
});

var vm = new Vue({
  el: '#vueapp',
  data:{
    userrequest: {},
    errors: []
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
          that.errors = data.errors;
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
