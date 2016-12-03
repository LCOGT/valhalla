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
var app = new Vue({
  el: '#vueapp',
  data: {
    proposals: [],
    userrequest: JSON.parse(JSON.stringify(userrequest))
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
          for (var key in data){
            if(data.hasOwnProperty(key)){
              for(i=0; i<data[key].length; i++){
                that.errors.add(key, data[key][i]);
              }
            }
          }
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
      this.userrequest.requests.push(JSON.parse(JSON.stringify(userrequest.requests[0])))
    }
  }
});


app.initialize();
