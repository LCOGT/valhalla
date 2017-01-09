/* globals $ Vue moment */
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

var errors = {
  non_field_errors: [],
  proposal: [],
  group_id: [],
  operator: [],
  ipp_value: [],
  observation_type: [],
  requests:[{
    target: {
      non_field_errors: [],
      name: [],
      type: [],
      ra: [],
      dec: [],
      proper_motion_ra: [],
      proper_motion_dec: [],
      epoch: [],
      parallax: [],
      scheme: [],
      orbinc: [],
      longascnode: [],
      argofperih: [],
      meandist: [],
      eccentricity: [],
      meananom: [],
    },
    molecules:[{
      non_field_errors: [],
      type: [],
      instrument_name: [],
      fitler: [],
      exposure_time: [],
      exposure_count: [],
      bin_x: [],
      bin_y: [],
      acquire_mode: [],
      acquire_radius_arcsec: []
    }],
    windows:[{
      non_field_errors: [],
      start: [],
      end: []
    }],
    location:{
      non_field_errors: [],
      telescope_class: []
    },
    constraints: {
      non_field_errors: [],
      max_airmass: [],
      min_lunar_distance: []
    }
  }]
};

var instrumentTypeMap = {
  '2M0-SCICAM-SPECTRAL': {'type': 'IMAGE', 'class': '2m0'},
  '2M0-FLOYDS-SCICAM': {'type': 'SPECTRA', 'class': '2m0'},
  '0M8-SCICAM-SBIG': {'type': 'IMAGE', 'class': '0m8'},
  '1M0-SCICAM-SINISTRO': {'type': 'IMAGE', 'class': '1m0'},
  '0M4-SCICAM-SBIG': {'type': 'IMAGE', 'class': '0m4'},
  '0M8-NRES-SCICAM': {'type': 'SPECTRA', 'class': '0m8'}
};

Vue.component('request-field', {
  props: ['size', 'id', 'label', 'value', 'errpath'],
  template: '<div class="control-group" :class="[{\'has-error\': errpath.length}, size]"> \
              <label :for="id">{{ label }}</label> \
              <div class="controls"> \
                <input :id=id class="form-control" v-bind:value="value" @input="$emit(\'input\', $event.target.value)"/> \
                  <span class="help-block text-danger" v-for="error in errpath">{{ error }}</span> \
                </div> \
            </div>'
});

var app = new Vue({
  el: '#vueapp',
  data: {
    hasError: true,
    proposals: [],
    instrumentTypes: {},
    duration: 0,
    userrequest: JSON.parse(JSON.stringify(userrequest)),
    errors: JSON.parse(JSON.stringify(errors)),
    advanced: false,
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
          that.errors = $.extend(true, JSON.parse(JSON.stringify(errors)), data.errors);
          that.duration = data.duration;
          that.hasError = (data.errors.length === 0) ? false: true;
        }
      });
    },
    initialize: function(){
      var that = this;
      $.getJSON('/api/profile/', function(data){
        that.proposals = data.proposals;
        for (var i = 0; i < data.available_instrument_types.length; i++) {
          var instrument_type = data.available_instrument_types[i];
          that.instrumentTypes[instrument_type] = {
            'type': instrumentTypeMap[instrument_type].type,
            'class': instrumentTypeMap[instrument_type].class,
            'name': instrument_type,
            'filters': [],
            'binnings': [],
            'default_binning': undefined
          };
        }
        that.validate();
      });
    },
    submitRequest: function(){
      var that = this;
      $.ajax({
        type: 'POST',
        url: '/api/user_requests/',
        data: JSON.stringify(that.userrequest),
        contentType: 'application/json',
        success: function(data){
          window.location = '/requests/' + data.id + '/';
        }
      });
    },
    addRequest: function(index){
      this.userrequest.requests.push(JSON.parse(JSON.stringify(this.userrequest.requests[index])));
      errors.requests.push(JSON.parse(JSON.stringify(errors.requests[index])));
      this.errors.requests.push(JSON.parse(JSON.stringify(this.errors.requests[index])));
      this.userrequest.operator = 'MANY';
      this.validate();
    },
    removeRequest: function(index){
      if(confirm('Are you sure you want to remove this request?')){
        this.userrequest.requests.splice(index, 1);
        this.errors.requests.splice(index, 1);
        if(this.userrequest.requests.length < 2){
          this.userrequest.operator = 'SINGLE';
        }
        this.validate();
      }
    },
    clearTargetFields: function(index){
      var fieldsToKeep = ['name', 'type'];
      for(var prop in this.userrequest.requests[index].target){
        if(fieldsToKeep.indexOf(prop) < 0){
          delete this.userrequest.requests[index].target[prop];
        }
      }
    },
    addMolecule: function(requestIndex, molIndex){
      this.userrequest.requests[requestIndex].molecules.push(
        JSON.parse(JSON.stringify(this.userrequest.requests[requestIndex].molecules[molIndex]))
      );
      errors.requests[requestIndex].molecules.push(
        JSON.parse(JSON.stringify(errors.requests[requestIndex].molecules[molIndex]))
      );
      this.errors.requests[requestIndex].molecules.push(
        JSON.parse(JSON.stringify(this.errors.requests[requestIndex].molecules[molIndex]))
      );
      this.validate();
    },
    removeMolecule: function(requestIndex, molIndex){
      if(confirm('Are you sure you wish to remove configuration #' + (molIndex + 1) + '?')){
        this.userrequest.requests[requestIndex].molecules.splice(molIndex, 1);
        this.errors.requests[requestIndex].molecules.splice(molIndex, 1);
        this.validate();
      }
    },
    addWindow: function(requestIndex, winIndex){
      this.userrequest.requests[requestIndex].windows.push(
        JSON.parse(JSON.stringify(this.userrequest.requests[requestIndex].windows[winIndex]))
      );
      errors.requests[requestIndex].windows.push(
        JSON.parse(JSON.stringify(errors.requests[requestIndex].windows[winIndex]))
      );
      this.errors.requests[requestIndex].windows.push(
        JSON.parse(JSON.stringify(this.errors.requests[requestIndex].windows[winIndex]))
      );
      this.validate();
    },
    removeWindow: function(requestIndex, winIndex){
      if(confirm('Are you sure you wish to remove window #' + (winIndex + 1) + '?')){
        this.userrequest.requests[requestIndex].windows.splice(winIndex, 1);
        this.errors.requests[requestIndex].windows.splice(winIndex, 1);
        this.validate();
      }
    },
    changeDataType: function(requestIndex){
      var request = this.userrequest.requests[requestIndex];
      request.instrument_name = this.selectFirstInstrumentForDataType(request.data_type);
      var new_mol = JSON.parse(JSON.stringify(userrequest.requests[0].molecules[0]));
      new_mol.type = (request.data_type === 'IMAGE') ? 'EXPOSE': 'SPECTRUM';
      new_mol.instrument_name = request.instrument_name;
      errors.requests[requestIndex].molecules = [JSON.parse(JSON.stringify(errors.requests[0].molecules[0]))];
      this.errors.requests[requestIndex].molecules = [JSON.parse(JSON.stringify(errors.requests[0].molecules[0]))];
      this.userrequest.requests[requestIndex].molecules = [new_mol];
      this.changeInstrument(requestIndex);

    },
    changeInstrument: function(requestIndex){
      var request = this.userrequest.requests[requestIndex];
      request.location.telescope_class = this.instrumentTypes[request.instrument_name].class;
      var that = this;
      $.getJSON('/api/instrument/' + request.instrument_name + '/', function(data){
        that.instrumentTypes[request.instrument_name].filters = data.filters;
        that.instrumentTypes[request.instrument_name].binnings = data.binnings;
        that.instrumentTypes[request.instrument_name].default_binning = data.default_binning;
        for (var i = 0; i < request.molecules.length; i++) {
          var mol = request.molecules[i];
          mol.bin_x = data.default_binning;
          mol.bin_y = data.default_binning;
          mol.instrument_name = request.instrument_name;
        }
      });
    },
    updateBinning: function(requestIndex, molIndex){
      var mol = this.userrequest.requests[requestIndex].molecules[molIndex];
      mol.bin_y = mol.bin_x;
    },
    selectFirstInstrumentForDataType: function(dataType){
      for(var instrumentType in this.instrumentTypes){
        if(this.instrumentTypes[instrumentType].type === dataType){
          return instrumentType;
        }
      }
      return '';
    }
  }
});


app.initialize();
