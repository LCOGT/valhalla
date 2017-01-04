/* globals $ Vue */
var userrequest = {
  proposal: '',
  group_id: '',
  operator: 'SINGLE',
  ipp_value: 1.0,
  observation_type: 'NORMAL',
  requests:[{
    data_type: 'IMAGE',
    target: {
      name: '',
      type: 'SIDEREAL',
      ra: '',
      dec: '',
      scheme: 'MPC_MINOR_PLANET'
    },
    molecules:[{
      type: 'EXPOSE',
      instrument_name: '',
      fitler: '',
      exposure_time: 30,
      exposure_count: 1,
      bin_x: 1,
      bin_y: 1
    }],
    windows:[{
      start: '2016-09-29T21:12:18Z',
      end: '2016-10-29T21:12:19Z'
    }],
    location:{
      telescope_class: '1m0'
    },
    constraints: {
      max_airmass: 2.0,
      min_lunar_distance: 30.0
    }
  }]
};

var errors = {
  proposal: [],
  group_id: [],
  operator: [],
  ipp_value: [],
  observation_type: [],
  requests:[{
    target: {
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
      type: [],
      instrument_name: [],
      fitler: [],
      exposure_time: [],
      exposure_count: [],
      bin_x: [],
      bin_y: []
    }],
    windows:[{
      start: [],
      end: []
    }],
    location:{
      telescope_class: []
    },
    constraints: {
      max_airmass: [],
      min_lunar_distance: []
    }
  }]
};

var allInstrumentTypes = {
  '2M0-SCICAM-SPECTRAL': 'IMAGE',
  '2M0-FLOYDS-SCICAM': 'SPECTRA',
  '0M8-SCICAM-SBIG': 'IMAGE',
  '1M0-SCICAM-SINISTRO': 'IMAGE',
  '0M4-SCICAM-SBIG': 'IMAGE',
  '0M8-NRES-SCICAM': 'SPECTRA'
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
    proposals: [],
    instrumentTypes: [],
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
          that.errors = $.extend(true, JSON.parse(JSON.stringify(errors)), data);
        }
      });
    },
    initialize: function(){
      var that = this;
      $.getJSON('/api/profile/', function(data){
        that.proposals = data.proposals;
        for (var i = 0; i < data.available_instrument_types.length; i++) {
          that.instrumentTypes.push(
            {'type': allInstrumentTypes[data.available_instrument_types[i]], 'name': data.available_instrument_types[i]}
          );
        }
      });
    },
    addRequest: function(index){
      this.userrequest.requests.push(JSON.parse(JSON.stringify(this.userrequest.requests[index])));
      errors.requests.push(JSON.parse(JSON.stringify(errors.requests[index])));
      this.errors.requests.push(JSON.parse(JSON.stringify(this.errors.requests[index])));
    },
    removeRequest: function(index){
      if(confirm('Are you sure you want to remove this request?')){
        this.userrequest.requests.splice(index, 1);
        this.errors.requests.splice(index, 1);
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
    },
    removeMolecule: function(requestIndex, molIndex){
      if(confirm('Are you sure you wish to remove configuration #' + (molIndex + 1) + '?')){
        this.userrequest.requests[requestIndex].molecules.splice(molIndex, 1);
        this.errors.requests[requestIndex].molecules.splice(molIndex, 1);
      }
    },
    changeDataType: function(requestIndex){
      var request = this.userrequest.requests[requestIndex];
      var new_mol = JSON.parse(JSON.stringify(userrequest.requests[0].molecules[0]));
      new_mol.type = (request.data_type === 'IMAGE') ? 'EXPOSE': 'SPECTRUM';
      if(request.molecules.length > 1){
        if(confirm('This is will remove all instrument configurations, are you sure?')){
          errors.requests[requestIndex].molecules = [JSON.parse(JSON.stringify(errors.requests[0].molecules[0]))];
          this.errors.requests[requestIndex].molecules = [JSON.parse(JSON.stringify(errors.requests[0].molecules[0]))];
          this.userrequest.requests[requestIndex].molecules = [new_mol];
        }else{
          request.data_type = (request.data_type === 'IMAGE') ? 'SPECTRA': 'IMAGE';
        }
      }else{
        request.molecules[0] = new_mol;
      }
    }
  }
});


app.initialize();
