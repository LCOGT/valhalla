/* globals $ Vue */
/* Notes
 * vee-validate seems nice, but getting it to work with nested forms may be an issue. Can't seem to index in templates.
 * May be worth just writing our own error bag class that just extends what the backend sends us.
 * See the validate method below
 * we may also be able to just connect custom validators to every field that needs it an parse the josn response
 */
var userrequest = {
  proposal: '',
  group_id: '',
  operator: 'SINGLE',
  ipp_value: 1.0,
  observation_type: 'NORMAL',
  requests:[{
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
      exposure_time: 0,
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
      orbinc: []
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

var app = new Vue({
  el: '#vueapp',
  data: {
    proposals: [],
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
      });
    },
    addRequest: function(){
      this.userrequest.requests.push(JSON.parse(JSON.stringify(this.userrequest.requests[0])));
      errors.requests.push(JSON.parse(JSON.stringify(errors.requests[0])));
      this.errors.requests.push(JSON.parse(JSON.stringify(this.errors.requests[0])));
    }
  }
});


app.initialize();
