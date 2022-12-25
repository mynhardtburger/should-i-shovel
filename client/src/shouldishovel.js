import Chart from 'chart.js/auto';
import 'chartjs-adapter-moment';

var chart = null;

function get_forecast(lat, lng) {
  // lat = document.getElementById('f_lat').value;
  // lon = document.getElementById('f_lon').value;

  fetch(`http://127.0.0.1:8000/forecast/?latitude=${lat}&longitude=${lng}`)
    .then((response) => response.json())
    .then((data) => {
      console.log(data);

      const chartData = {
        labels: Object.values(data['forecast_time']),
        datasets: [
          {
            label: data['long_name'][0],
            data: Object.values(data['value']),
            borderColor: 'rgb(255, 99, 132)',
            fill: false,
            cubicInterpolationMode: 'monotone',
            tension: 0.4,
          },
        ],
      };

      if (chart === null) {
        chart = draw_chart(chartData);
      } else {
        chart.data.labels = chartData.labels;
        chart.data.datasets = chartData.datasets;
        chart.update();
      }
    })
    .catch(console.error);
}

function draw_chart(chartdata) {
  return new Chart(document.getElementById('charts'), {
    type: 'line',
    data: chartdata,
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: '48 hour forecast',
        },
        legend: {
          display: false,
        },
      },
      interaction: {
        intersect: false,
      },
      scales: {
        x: {
          display: true,
          title: {
            display: true,
          },
          type: 'timeseries',
          time: {
            displayFormats: {
              hour: 'DD MMM hh:mm A',
            },
            unit: 'hour',
            unitStepSize: 1,
          },
        },
        y: {
          display: true,
          title: {
            display: true,
            text: 'Meters',
          },
          suggestedMin: 0,
          suggestedMax: 1,
        },
      },
    },
  });
}

function get_forecast_for_address() {
  address = document.getElementById('address').value;

  fetch(`http://127.0.0.1:8000/address/?address=${address}`)
    .then((response) => response.json())
    .then((coords) => {
      console.log(coords);
      if (coords[0] === null) {
        console.log('No coordinates found');
      } else {
        get_forecast(coords[0], coords[1]);
      }
    })
    .catch(console.error);
}

const button = document.getElementById('getData');
const button_address = document.getElementById('getData_address');
button.addEventListener('click', () =>
  get_forecast(
    document.getElementById('f_lat').value,
    document.getElementById('f_lng').value
  )
);
button_address.addEventListener('click', get_forecast_for_address);
