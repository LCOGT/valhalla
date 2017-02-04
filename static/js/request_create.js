/* globals _ $ Vue moment vis Utils */

var datetimeFormat = 'YYYY-M-D HH:mm:ss';

var instrumentTypeMap = {
  '2M0-SCICAM-SPECTRAL': {type: 'IMAGE', class: '2m0', filters: [], binnings: [], default_binning: null},
  '2M0-FLOYDS-SCICAM': {type: 'SPECTRA', class: '2m0', filters: [], binnings: [], default_binning: null},
  '0M8-SCICAM-SBIG': {type: 'IMAGE', class: '0m8', filters: [], binnings: [], default_binning: null},
  '1M0-SCICAM-SINISTRO': {type: 'IMAGE', class: '1m0', filters: [], binnings: [], default_binning: null},
  '0M4-SCICAM-SBIG': {type: 'IMAGE', class: '0m4', filters: [], binnings: [], default_binning: null},
  '0M8-NRES-SCICAM': {type: 'SPECTRA', class: '0m8', filters: [], binnings: [], default_binning: null}
};

var collapseMixin = {
  watch: {
    parentshow: function(value){
      this.show = value;
    }
  }
};

Vue.component('userrequest', {
  props: ['errors', 'userrequest', 'duration_data'],
  data: function(){
    return {
        show: true,
        showCadence: false,
        cadenceRequests: [],
        available_instruments: [],
        proposals: [],
        cadenceRequestId: -1
    };
  },
  created: function(){
    var that = this;
    $.getJSON('/api/profile/', function(data){
      that.proposals = data.proposals;
      that.available_instruments = data.available_instrument_types;
      that.update();
    });
  },
  computed:{
    proposalOptions: function(){
      return _.sortBy(_.map(this.proposals, function(p){return {'value': p, 'text': p};}), 'text');
    },
    'userrequest.operator': function(){
      return this.userrequest.requests.length > 1 ? 'MANY' : 'SINGLE';
    },
    durationDisplay: function(){
      var duration =  moment.duration(this.duration_data.duration, 'seconds');
      return duration.hours() + ' hours ' + duration.minutes() + ' minutes ' + duration.seconds() + ' seconds';
    }
  },
  methods: {
    update: function(){
      this.$emit('userrequestupdate');
    },
    requestUpdated: function(data){
      console.log('request updated');
      this.update();
    },
    addRequest: function(idx){
      var newRequest = _.cloneDeep(this.userrequest.requests[idx]);
      this.userrequest.requests.push(newRequest);
      this.update();
    },
    removeRequest: function(idx){
      this.userrequest.requests.splice(idx, 1);
      this.update();
    },
    expandCadence: function(data){
      if(!_.isEmpty(this.errors)){
        alert('Please make sure your request is valid before generating a cadence');
        return false;
      }
      this.cadenceRequestId = data.id;
      var payload = this.userrequest;
      payload.requests = [data.request];
      payload.requests[data.id].windows = [];
      payload.requests[data.id].cadence = data.cadence;
      var that = this;
      $.ajax({
        type: 'POST',
        url: '/api/user_requests/cadence/',
        data: JSON.stringify(payload),
        contentType: 'application/json',
        success: function(data){
          for(var r in data.requests){
            that.cadenceRequests.push(data.requests[r]);
          }
        }
      });
      this.showCadence = true;
    },
    cancelCadence: function(){
      this.cadenceRequests = [];
      this.cadenceRequestId = -1;
      this.showCadence = false;
    },
    acceptCadence: function(){
      // this is a bit hacky because the UI representation of a request doesnt match what the api expects/returns
      var that = this;
      for(var r in this.cadenceRequests){
        // all that changes in the cadence is the window, so instead of parsing what is returned we just copy the request
        // that the cadence was generated from and replace the window from what is returned.
        var newRequest = _.cloneDeep(that.userrequests.requests[that.cadenceRequestId]);
        newRequest.windows = that.cadenceRequests[r].windows;
        delete newRequest.cadence;
        that.requests.push(newRequest);
      }
      // finally we remove the original request
      this.removeRequest(that.cadenceRequestId);
      if(this.userrequest.requests.length > 1) this.operator = 'MANY';
      this.cadenceRequests = [];
      this.cadenceRequestId = -1;
      this.showCadence = false;
      this.update();
    }
  },
  template: '#userrequest-template'
});

Vue.component('request', {
  props: ['request', 'index', 'errors', 'iavailable_instruments', 'parentshow', 'duration_data'],
  mixins: [collapseMixin],
  data: function(){
    return {show: true,
            data_type: 'IMAGE',
            instrument_name: ''};
  },
  computed: {
    availableInstrumentOptions: function(){
      var options = [];
      for(var i in this.iavailable_instruments){
        var instrument_name = this.iavailable_instruments[i];
        if(instrumentTypeMap[instrument_name].type === this.data_type){
          options.push({value: instrument_name, text: instrument_name});
        }
      }
      return _.sortBy(options, 'text').reverse();
    },
    firstAvailableInstrument: function(){
      return this.availableInstrumentOptions[0].value;
    }
  },
  watch: {
    data_type: function(){
      if(instrumentTypeMap[this.instrument_name].type != this.data_type){
        this.instrument_name = this.firstAvailableInstrument;
        this.update();
      }
    },
    instrument_name: function(value){
      if(value){
        this.request.location.telescope_class = vm.instrumentTypeMap[value].class;
        $.getJSON('/api/instrument/' + value + '/', function(data){
          vm.instrumentTypeMap[value].filters = data.filters;
          vm.instrumentTypeMap[value].binnings = data.binnings;
          vm.instrumentTypeMap[value].default_binning = data.default_binning;
        });
      }
    },
    iavailable_instruments: function(){
      if(!this.instrument_name){
        this.instrument_name = this.firstAvailableInstrument;
      }
    }
  },
  methods: {
    update: function(){
      this.$emit('requestupdate', {'id': this.index});
    },
    moleculeFillWindow: function(data){
      console.log('moleculefillwindow');
      if('largest_interval' in this.duration_data){
        var num_exposures = this.request.molecules[data.id].exposure_count;
        var molecule_duration = this.duration_data.molecules[data.id].duration;
        var available_time = this.duration_data.largest_interval - this.duration_data.duration + (molecule_duration*num_exposures);
        num_exposures = Math.floor(available_time / molecule_duration);
        this.request.molecules[data.id].exposure_count = Math.max(1, num_exposures);
        this.update();
      }
    },
    moleculeUpdated: function(data){
      console.log('moleculeupdated');
      this.update();
    },
    windowUpdated: function(data){
      console.log('windowUpdated');
      this.update();
    },
    targetUpdated: function(data){
      console.log('targetUpdated');
      this.update();
    },
    constraintsUpdated: function(data){
      console.log('constraintsUpdated');
      this.update();
    },
    addWindow: function(idx){
      var newWindow = JSON.parse(JSON.stringify(this.request.windows[idx]));
      this.request.windows.push(newWindow);
      this.update();
    },
    addMolecule: function(idx){
      var newMolecule = JSON.parse(JSON.stringify(this.request.molecules[idx]));
      this.request.molecules.push(newMolecule);
      this.update();
    },
    removeWindow: function(idx){
      this.request.windows.splice(idx, 1);
      this.update();
    },
    removeMolecule: function(idx){
      this.request.molecules.splice(idx, 1);
      this.update();
    },
    cadence: function(data){
      this.$emit('cadence', {'id': this.index, 'request':this.request, 'cadence': data});
    }
  },
  template: '#request-template'
});

Vue.component('molecule', {
  props: ['molecule', 'index', 'errors', 'selectedinstrument', 'datatype', 'parentshow', 'duration_data'],
  mixins: [collapseMixin],
  data: function(){
    var acquire_params = {acquire_mode: 'OFF',
          acquire_radius_arcsec: null
          }
    return {'show': true, acquire_params: acquire_params};
  },
  computed: {
    filterOptions: function(){
      var options = [{value: '', text: ''}];
      var filters = _.get(this.$root.instrumentTypeMap, [this.selectedinstrument, 'filters'], []);
      for(var filter in filters){
        if(['Standard', 'Slit', 'VirtualSlit'].indexOf(filters[filter].type) > -1){ // TODO select on mode
          options.push({value: filter, text: filters[filter].name});
        }
      }
      return _.sortBy(options, 'text');
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
      this.$emit('moleculeupdate', {'id': this.index});
    },
    binningsUpdated: function(){
      this.molecule.bin_y = this.molecule.bin_x;
      this.update();
    },
    fillWindow: function(){
    console.log("fillWindow");
      this.$emit('moleculefillwindow', {'id': this.index});
    }
  },
  watch: {
    selectedinstrument: function(value){
      this.molecule.instrument_name = value;
      this.molecule.filter = '';
      // wait for options to update, then set default
      var that = this;
      setTimeout(function(){
        var default_binning = _.get(that.$root.instrumentTypeMap, [that.selectedinstrument, 'default_binning'], null);
        that.molecule.bin_x = default_binning;
        that.molecule.bin_y = default_binning;
        that.update();
      }, 100);
    },
    datatype: function(value){
      this.molecule.type = (value === 'IMAGE') ? 'EXPOSE': 'SPECTRUM';
      if (this.datatype === 'SPECTRA'){
        this.molecule.acquire_mode = this.acquire_params.acquire_mode;
        if (this.molecule.acquire_mode === 'BRIGHTEST'){
            this.molecule.acquire_radius_arcsec = this.acquire_params.acquire_radius_arcsec;
        }
      }
      else{
        this.acquire_params.acquire_mode = this.molecule.acquire_mode;
        this.molecule.acquire_mode = undefined;
        this.molecule.acquire_radius_arcsec = undefined;
      }
    },
    'molecule.acquire_mode': function(value){
        if(this.molecule.acquire_mode === 'BRIGHTEST'){
            this.molecule.acquire_radius_arcsec = this.acquire_params.acquire_radius_arcsec;
        }
        else{
            if(typeof this.molecule.acquire_radius_arcsec != undefined){
                this.acquire_params.acquire_radius_arcsec = this.molecule.acquire_radius_arcsec;
                this.molecule.acquire_radius_arcsec = undefined;
            }
        }
    }
  },
  template: '#molecule-template'
});

Vue.component('target', {
  props: ['target', 'errors', 'datatype', 'parentshow'],
  mixins: [collapseMixin],
  data: function(){
    var ns_target_params = {scheme: 'MPC_MINOR_PLANET',
          orbinc: 0,
          longascnode: 0,
          argofperih: 0,
          meandist: 0,
          eccentricity: 0,
          meananom: 0
          }
    var rot_target_params = {rot_mode: 'SKY', rot_angle: 0}
    var sid_target_params = _.cloneDeep(this.target);
    delete sid_target_params['name']
    delete sid_target_params['epoch']
    delete sid_target_params['type']
    return {show: true, lookingUP: false, ns_target_params: ns_target_params, sid_target_params: sid_target_params, rot_target_params: rot_target_params};
  },
  methods: {
    update: function(){
      this.$emit('targetupdate', {});
    },
    updateRA: function(){
      this.ra = Utils.sexagesimalRaToDecimal(this.ra);
      this.update();
    },
    updateDec: function(){
      this.dec = Utils.sexagesimalDecToDecimal(this.dec);
      this.update();
    }
  },
  watch: {
    'target.name': _.debounce(function(name){
      this.lookingUP = true;
      var that = this;
      $.getJSON('https://lco.global/lookUP/json/?name=' + name).done(function(data){
        that.target.ra = _.get(data, ['ra', 'decimal'], null);
        that.target.dec = _.get(data, ['dec', 'decimal'], null);
        that.target.proper_motion_ra = data.pmra;
        that.target.proper_motion_dec = data.pmdec;
        that.update();
      }).always(function(){
        that.lookingUP = false;
      });
    }, 500),
    'datatype': function(value){
        if(this.datatype === 'SPECTRA'){
            for (var param in this.rot_target_params){
                this.target[param] = this.rot_target_params[param];
            }
        }
        else{
            for (var param in this.rot_target_params){
                this.rot_target_params[param] = this.target[param];
                this.target[param] = undefined;
            }
        }
    },
    'target.type': function(value){
        that = this;
        if(this.target.type === 'SIDEREAL'){
            for (var param in this.ns_target_params){
                that.ns_target_params[param] = that.target[param];
                that.target[param] = undefined;
            }
            for (var param in this.sid_target_params){
                that.target[param] = that.sid_target_params[param];
            }
        }else if(this.target.type === 'NON_SIDEREAL'){
            for (var param in this.sid_target_params){
                that.sid_target_params[param] = that.target[param];
                that.target[param] = undefined;
            }
            for (var param in this.ns_target_params){
                that.target[param] = that.ns_target_params[param];
            }
        }
    }
  },
  template: '#target-template'
});

Vue.component('window', {
  props: ['window', 'index', 'errors', 'parentshow'],
  mixins: [collapseMixin],
  data: function(){
    return {show: true,
        cadence: false,
        period: 24.0,
        jitter: 12.0};
  },
  methods: {
    update: function(){
      this.$emit('windowupdate', {'id': this.index, 'data': this.toRep});
    },
    genCadence: function(){
      this.$emit('cadence', {'start': this.window.start, 'end': this.window.end, 'period': this.period, 'jitter': this.jitter});
    }
  },
  template: '#window-template'
});

Vue.component('constraints', {
  props: ['constraints', 'errors', 'parentshow'],
  mixins: [collapseMixin],
  data: function(){
    return {'show': true};
  },
  methods: {
    update: function(){
      this.$emit('constraintsupdate', {'data': this.toRep});
    }
  },
  template: '#constraints-template'
});

Vue.component('cadence', {
  props: ['data'],
  data: function(){
    return {
      options: {},
      items: this.toVis
    };
  },
  computed:{
    toVis: function(){
      var visData = [];
      for(var r in this.data){
        var request = this.data[r];
        visData.push({'id': r, content: '' + (Number(r) + 1), start: request.windows[0].start, end: request.windows[0].end});
      }
      return new vis.DataSet(visData);
    }
  },
  watch: {
    data: function(){
      this.timeline.setItems(this.toVis);
      this.timeline.fit();
    }
  },
  mounted: function(){
    this.timeline = new vis.Timeline(this.$el, this.items, this.options);
  },
  template: '<div class="cadencetimeline"></div>'
});

Vue.component('modal', {
  props: ['show', 'header'],
  data: function(){
    return {
      open: false
    };
  },
  methods: {
    close: function(){
      this.open = false;
      this.$emit('close');
    },
    submit: function(){
      this.open = false;
      this.$emit('submit');
    }
  },
  watch: {
    show: function(value){
      this.open = value;
    }
  },
  computed: {
    modalStyle: function(){
      return this.open ? { 'padding-left': '0px;', display: 'block' } : {};
    }
  },
  template: '#modal-template'
});

Vue.component('custom-field', {
  props: ['value', 'label', 'field', 'errors', 'type'],
  mounted: function(){
    var that = this;
    if(this.type === 'datetime'){
      $(this.$el).find('input').datetimepicker({
        format: datetimeFormat,
        minDate: moment().subtract(1, 'days'),
        keyBinds: {left: null, right: null, up: null, down: null}
      }).on('dp.change', function(e){
        that.update(moment(e.date).format(datetimeFormat));
      });
    }
  },
  methods: {
    update: function(value){
      this.$emit('input', value);
    },
    blur: function(value){
      this.$emit('blur', value);
    }
  },
  template: '#custom-field'
});

Vue.component('custom-select', {
  props: ['value', 'label', 'field', 'options', 'errors'],
  methods: {
    update: function(value){
      this.$emit('input', value);
    },
    isSelected: function(option){
      return option === this.value;
    }
  },
  template: '#custom-select'
});

Vue.component('sidenav', {
  props: ['userrequest'],
  template: '#sidenav-template'
});

Vue.component('drafts', {
  props: ['tab'],
  data: function(){
    return {'drafts': []};
  },
  methods: {
    fetchDrafts: function(){
      var that = this;
      $.getJSON('/api/drafts/', function(data){
        that.drafts = data.results;
      });
    },
    loadDraft: function(id){
      this.$emit('loaddraft', id);
    },
    deleteDraft: function(id){
      if(confirm('Are you sure you want to delete this draft?')){
        var that = this;
        $.ajax({
          type: 'DELETE',
          url: '/api/drafts/' + id + '/'
        }).done(function(){
          that.fetchDrafts();
        });
      }
    }
  },
  watch: {
    tab: function(value){
      if(value === 3) this.fetchDrafts();
    }
  },
  template: '#drafts-template'
});

Vue.component('alert', {
  props: ['alertclass'],
  template: '#alert-template'
});

Vue.filter('formatDate', function(value){
  if(value){
    return moment(String(value)).format(datetimeFormat);
  }
});

var vm = new Vue({
  el: '#vueapp',
  data:{
    tab: 1,
    draftId: -1,
    instrumentTypeMap: instrumentTypeMap,
    userrequest: {
      group_id: '',
      proposal: '',
      ipp_value: 1.05,
      operator: 'SINGLE',
      observation_type: 'NORMAL',
      requests: [{
        target: {
          name: '',
          type: 'SIDEREAL',
          ra: 0,
          dec: 0,
          proper_motion_ra: 0.0,
          proper_motion_dec: 0.0,
          epoch: 2000,
          parallax: 0,
        },
        molecules:[{
          type: 'EXPOSE',
          instrument_name: '',
          filter: '',
          exposure_time: 30,
          exposure_count: 1,
          bin_x: null,
          bin_y: null,
          fill_window: false,
        }],
        windows:[{
          start: moment().format(datetimeFormat),
          end: moment().format(datetimeFormat)
        }],
        location:{
          telescope_class: ''
        },
        constraints: {
          max_airmass: 2.0,
          min_lunar_distance: 30.0
        }
      }]
    },
    errors: {},
    duration_data: {},
    alerts: []
  },
  methods: {
    validate: _.debounce(function(){
      var that = this;
      $.ajax({
        type: 'POST',
        url: '/api/user_requests/validate/',
        data: JSON.stringify(that.userrequest),
        contentType: 'application/json',
        success: function(data){
          that.errors = data.errors;
          that.duration_data = data.request_durations;
        }
      });
    }, 200),
    submit: function(){
      var that = this;
      $.ajax({
        type: 'POST',
        url: '/api/user_requests/',
        data: JSON.stringify(that.userrequest),
        contentType: 'application/json',
        success: function(data){
          window.location = '/requests/' + data.id;
        }
      });
    },
    userrequestUpdated: function(data){
      console.log('userrequest updated');
      this.validate();
    },
    saveDraft: function(id){
      if(!this.userrequest.group_id || !this.userrequest.proposal){
        alert('Please give your draft a title and proposal');
        return;
      }
      var url = '/api/drafts/';
      var method = 'POST';

      if(id > -1){
        url += id + '/';
        method = 'PUT';
      }
      var that = this;
      $.ajax({
        type: method,
        url: url,
        data: JSON.stringify({
          proposal: that.userrequest.proposal,
          title: that.userrequest.group_id,
          content: JSON.stringify(that.userrequest)
        }),
        contentType: 'application/json',
      }).done(function(data){
        that.draftId = data.id;
        that.alerts.push({class: 'alert-success', msg: 'Draft id: ' + data.id + ' saved successfully.' });
        console.log('Draft saved ' + that.draftId);
      }).fail(function(data){
        for(var error in data.responseJSON.non_field_errors){
          that.alerts.push({class: 'alert-danger', msg: data.responseJSON.non_field_errors[error]});
        }
      });
    },
    loadDraft: function(id){
      this.draftId = id;
      this.tab = 1;
      var that = this;
      $.getJSON('/api/drafts/' + id + '/', function(data){
        that.userrequest = JSON.parse(data.content);
        that.validate();
      });
    }
  }
});

$('body').scrollspy({
  target: '.bs-docs-sidebar',
  offset: 180
});
