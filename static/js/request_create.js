/* globals $ Vue */

var app = new Vue({
  el: '#vueapp',
  data: {
    errors: {},
    proposals: [],
    userrequest: {
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
          dec: ''
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
    }
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
          that.errors = data;
        }
      });
    },
    initialize: function(){
      var that = this;
      $.getJSON('/api/profile/', function(data){
        that.proposals = data.proposals;
      });
    }
  }
});


app.initialize();
