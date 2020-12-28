
var location_data = JSON.parse('{{ location_data | tojson | safe}}');
var station_data = JSON.parse('{{ station_data | tojson | safe}}');

var weekday_totals = JSON.parse('{{ weekday_totals | tojson | safe}}');
var hour_totals = JSON.parse('{{ weekday_totals | tojson | safe}}');

var ctx = document.getElementById('data-chart').getContext('2d');
var ctx3 = document.getElementById('time-chart').getContext('2d');
var timeFormat = 'YYYY-MM-DD h:mm:ss.SSS';

new Chart(document.getElementById('week-chart').getContext('2d'), {
type: 'horizontalBar',
data: {
  labels: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
  datasets: [
    {
      label: "Total Samples",
      backgroundColor: ["#3e95cd", "#8e5ea2","#3cba9f","#e8c3b9","#c45850"],
      data: weekday_totals
    }
  ]
},
options: {

  responsive: true,
    maintainAspectRatio: false,
  legend: { display: false 
  },
  title: {
    display: true,
    text: 'Predicted world population (millions) in 2050'
  }
}
});
new Chart(ctx3, {
type: 'horizontalBar',
data: {
  labels: ["Africa", "Asia", "Europe", "Latin America", "North America"],
  datasets: [
    {
      label: "Population (millions)",
      backgroundColor: ["#3e95cd", "#8e5ea2","#3cba9f","#e8c3b9","#c45850"],
      data: [2478,5267,734,784,433]
    }
  ]
},
options: {

  responsive: true,
    maintainAspectRatio: false,
  legend: { display: false 
  },
  title: {
    display: true,
    text: 'Predicted world population (millions) in 2050'
  }
}
});
/////////Main Chart/////////
var chart = new Chart(ctx, {
  // The type of chart we want to create
  type: 'line',
  data: location_data,

  // Configuration options go here
  options: {
    responsive: true,
    maintainAspectRatio: false,
    title: {
      display: false,
    },
    legend: {
      display: true,
      position: "right",
      onClick: location_legend,
      labels: {
        usePointStyle: true,
        fontColor: '#FFFFFF',
        fontSize: 15,
        padding: 20,
        fontStyle: 'bold'
      }
    },
    scales: {
      xAxes: [{
        type: "time",
        time: {
          format: timeFormat,
          tooltipFormat: 'll'
        },
        scaleLabel: {
          display: true,
          labelString: 'Date'
        }
      }],
      yAxes: [{
        scaleLabel: {
          display: false,
        }
      }]
    }
  }
}
);

function station_legend(e, legendItem) {
  chart.config.data = location_data;
  chart.config.options.legend.onClick = location_legend;
  $('#chart-title').text("Location Activity");
  chart.update();
};

function location_legend(e, legendItem) {
  $('#chart-title').text("Station Activity @ " + chart.data.datasets[legendItem.datasetIndex].label);
  chart.config.data = station_data[legendItem.datasetIndex];
  chart.config.options.legend.onClick = station_legend;
  chart.update();
};