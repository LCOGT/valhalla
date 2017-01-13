/* globals _ $ Vue moment */

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
  props: ['index', 'errors'],
  data: function(){
    return {
      start: moment().format('YYYY-M-D HH:mm:ss'),
      end: moment().format('YYYY-M-D HH:mm:ss'),
    };
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

Vue.component('request', {
  props: ['idx', 'errors'],
  data: function(){
    return {
      windows: [{}],
      molecules: [{}],
      index: this.idx
    };
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
  props: ['errors'],
  data: function(){
    return {
      // requests: this.irequests,
      group_id: '',
      proposal: '',
      operator: 'SINGLE',
      ipp_value: 1,
      observation_type: 'NORMAL',
      requests: [{}]
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
    addRequest: function(){
      var newRequest = JSON.parse(JSON.stringify(this.requests[0]));
      this.requests.push(newRequest);
    },
  },
  template: '#userrequest-template'
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
