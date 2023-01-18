import Chart from 'chart.js/auto';
import 'chartjs-adapter-moment';
import _ from 'lodash';

var chart = null;

export function get_forecast(lat, lng) {
  // lat = document.getElementById('f_lat').value;
  // lon = document.getElementById('f_lon').value;

  fetch(
    `http://127.0.0.1:8000/forecast/coordinates?latitude=${lat}&longitude=${lng}`
  )
    .then((response) => response.json())
    .then((data) => {
      console.log(data);

      for (let forecast_var of data) {
        const chartData = {
          labels: Object.values(forecast_var['forecast_timestamp']),
          datasets: [
            {
              label: forecast_var['variable'][0],
              data: Object.values(forecast_var['value']),
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
          // chart.data.labels = chartData.labels;
          // chart.data.datasets = chartData.datasets;
          // chart.update();
        }
      }
    })
    .catch(console.error);
}

export function draw_chart(chartdata) {
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

export function get_forecast_for_address() {
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
