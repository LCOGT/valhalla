/* globals _ $ Vue moment */

var instrumentTypeMap = {
  '2M0-SCICAM-SPECTRAL': {type: 'IMAGE', class: '2m0', filters: [], binnings: [], default_binning: null},
  '2M0-FLOYDS-SCICAM': {type: 'SPECTRA', class: '2m0', filters: [], binnings: [], default_binning: null},
  '0M8-SCICAM-SBIG': {type: 'IMAGE', class: '0m8', filters: [], binnings: [], default_binning: null},
  '1M0-SCICAM-SINISTRO': {type: 'IMAGE', class: '1m0', filters: [], binnings: [], default_binning: null},
  '0M4-SCICAM-SBIG': {type: 'IMAGE', class: '0m4', filters: [], binnings: [], default_binning: null},
  '0M8-NRES-SCICAM': {type: 'SPECTRA', class: '0m8', filters: [], binnings: [], default_binning: null}
};

Vue.component('userrequest', {
  props: ['errors'],
  data: function(){
    return {
      proposals: [],
      available_instruments: [],
      group_id: '',
      proposal: '',
      operator: 'SINGLE',
      ipp_value: 1,
      observation_type: 'NORMAL',
      requests: [{
        data_type: '',
        instrument_type: '',
        target: {
          name: '',
          type: 'SIDEREAL',
          ra: 0,
          dec: 0,
          scheme: 'MPC_MINOR_PLANET',
          proper_motion_ra: 0.0,
          proper_motion_dec: 0.0,
          epoch: 2000,
          parallax: 0,
          orbinc: 0,
          longascnode: 0,
          argofperih: 0,
          meandist: 0,
          eccentricity: 0,
          meananom: 0
        },
        molecules:[{
          type: 'EXPOSE',
          instrument_type: '',
          filter: '',
          exposure_time: 30,
          exposure_count: 1,
          bin_x: null,
          bin_y: null,
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
  created: function(){
    var that = this;
    $.getJSON('/api/profile/', function(data){
      that.proposals = data.proposals;
      that.available_instruments = data.available_instrument_types;
    });
  },
  computed:{
    toRep: function(){
      var rep = {};
      var that = this;
      ['group_id', 'proposal', 'operator', 'ipp_value', 'observation_type', 'requests'].forEach(function(x){
        rep[x] = that[x];
      });
      return rep;
    },
    proposalOptions: function(){
      return _.map(this.proposals, function(p){return {'value': p, 'text': p};});
    }
  },
  methods: {
    update: function(){
      this.$emit('userrequestupdate', this.toRep);
    },
    requestUpdated: function(data){
      console.log('request updated')
      Vue.set(this.requests, data.id, data.data);
      this.update();
    },
    addRequest: function(idx){
      var newRequest = JSON.parse(JSON.stringify(this.requests[idx]));
      this.requests.push(newRequest);
    },
  },
  template: '#userrequest-template'
});

Vue.component('request', {
  props: ['irequest', 'index', 'errors', 'iavailable_instruments'],
  data: function(){
    return this.irequest;
  },
  computed: {
    toRep: function(){
      var rep = {};
      var that = this;
      ['target', 'molecules', 'windows', 'location', 'constraints'].forEach(function(x){
        rep[x] = that[x];
      });
      return rep;
    },
    availableInstrumentOptions: function(){
      var defaultText = this.data_type ? 'Please select an instrument' : 'Please select a data type';
      var options = [{value: '', text: defaultText}];
      for(var i in this.iavailable_instruments){
        var instrument_type = this.iavailable_instruments[i];
        if(instrumentTypeMap[instrument_type].type === this.data_type){
          options.push({value: instrument_type, text: instrument_type});
        }
      }
      return options;
    }
  },
  watch: {
    instrument_type: function(value){
      $.getJSON('/api/instrument/' + value + '/', function(data){
        vm.instrumentTypeMap[value].filters = data.filters;
        vm.instrumentTypeMap[value].binnings = data.binnings;
        vm.instrumentTypeMap[value].default_binning = data.default_binning;
      });
    }
  },
  methods: {
    update: function(){
      this.$emit('requestupdate', {'id': this.index, 'data': this.toRep});
    },
    moleculeUpdated: function(data){
      Vue.set(this.molecules, data.id, data.data);
      console.log('moleculeupdated')
      this.update();
    },
    windowUpdated: function(data){
      Vue.set(this.windows, data.id, data.data);
      console.log('windowUpdated')
      this.update();
    },
    targetUpdated: function(data){
      this.target = data.data;
      console.log('tafgetUpdated')
      this.update();
    },
    addWindow: function(idx){
      var newWindow = JSON.parse(JSON.stringify(this.windows[idx]));
      this.windows.push(newWindow);
      this.update();
    },
    addMolecule: function(idx){
      var newMolecule = JSON.parse(JSON.stringify(this.molecules[idx]));
      this.molecules.push(newMolecule);
      this.update();
    }
  },
  template: '#request-template'
});

Vue.component('molecule', {
  props: ['imolecule', 'index', 'errors', 'selectedinstrument'],
  data: function(){
    return this.imolecule;
  },
  computed: {
    toRep: function(){
      return this.$data;
    },
    filterOptions: function(){
      var options = [];
      var filters = _.get(this.$root.instrumentTypeMap, [this.selectedinstrument, 'filters'], []);
      filters.forEach(function(filter){
        options.push({value: filter, text: filter});
      });
      return options;
    },
    binningsOptions: function(){
      var options = [];
      var binnings = _.get(this.$root.instrumentTypeMap, [this.selectedinstrument, 'binnings'], []);
      binnings.forEach(function(binning){
        options.push({value: binning, text: binning});
      });
      return options;
    },
  },
  methods: {
    update: function(){
      this.$emit('moleculeupdate', {'id': this.index, 'data': this.toRep});
    },
    binningsUpdated: function(){
      this.bin_y = this.bin_x;
      this.update();
    }
  },
  watch: {
    selectedinstrument: function(value){
      this.instrument_type = value;
      // wait for options to update, then set default
      var that = this;
      setTimeout(function(){
        var default_binning = _.get(that.$root.instrumentTypeMap, [that.selectedinstrument, 'default_binning'], null);
        that.bin_x = default_binning;
        that.bin_y = default_binning;
        that.update();
      }, 100);
    }
  },
  template: '#molecule-template'
});

Vue.component('target', {
  props: ['itarget', 'errors'],
  data: function(){
    return this.itarget;
  },
  computed: {
    toRep: function(){
      var rep = {'name': this.name, 'type': this.type};
      var that = this;
      if(this.type === 'SIDEREAL'){
        ['ra', 'dec', 'proper_motion_ra', 'proper_motion_dec', 'epoch', 'parallax'].forEach(function(x){
          rep[x] = that[x];
        });
      }else if(this.type === 'NON_SIDEREAL'){
        ['scheme', 'epoch', 'orbinc', 'longascnode', 'argofperih', 'meandist', 'eccentricity', 'meananom'].forEach(function(x){
          rep[x] = that[x];
        });
      }
      return rep;
    }
  },
  methods: {
    update: function(){
      this.$emit('targetupdate', {'data': this.toRep});
    }
  },
  template: '#target-template'
});

Vue.component('window', {
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
    instrumentTypeMap: instrumentTypeMap,
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
