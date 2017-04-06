export default {
  data: {
    instrument: '1M0-SCICAM-SINISTRO',
  },
  name: 'contention',
  created: function(){
      this.api_call(function(keys, values) {
      var ctx = document.getElementById('myChart');
      var allData = {
          type: 'bar',
          data: {
              labels: keys,
              datasets: [{
                  data: values,
                  backgroundColor:
                      'rgba(255, 99, 132, 0.7)',
                  borderWidth: 1
              }]
          },
          options: {
              legend: {
              display: false
          },
              scales: {
                  yAxes: [{
                      ticks: {
                          beginAtZero:true,
                          scaleSteps:.25
                      },
                      barPercentage:1,
                      categoryPercentage:.95,
                      scaleLabel: {
                          display: true,
                          labelString: 'Total Requested Hours'
                      }
                  }],
                  xAxes: [{
                      ticks: {
                          stepSize: 2
                      },
                  barPercentage:1,
                  categoryPercentage:.9
                  }],
              },
          }
      }
      myChart = new Chart(ctx, allData);
      });
    },
  methods: {
    api_call: function(callback){
      $.getJSON('/api/contention/' + this.instrument, function (json) {
        var keys = Object.keys(json).map(function(key) {
          return key;
        });
        var values = Object.values(json).map(function(values) {
          return (values['All Proposals'] / 3600).toFixed(3);
        });
        callback(keys, values)
      });
    },
    update_chart: function(callback){
      this.api_call(function(keys, values) {
      myChart.data.labels = keys;
      myChart.data.datasets[0].data = values; 
      myChart.update(); 
    });
    }
  }
}