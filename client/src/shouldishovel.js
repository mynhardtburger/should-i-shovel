import Chart from 'chart.js/auto';
import 'chartjs-adapter-moment';
import _ from 'lodash';
import annotationPlugin from 'chartjs-plugin-annotation';

Chart.register(annotationPlugin);

let charts = {};

export function getForecast(lat, lng) {
  // lat = document.getElementById('f_lat').value;
  // lon = document.getElementById('f_lon').value;

  fetch(
    `http://127.0.0.1:8000/forecast/coordinates?latitude=${lat}&longitude=${lng}`
  )
    .then((response) => response.json())
    .then((data) => {
      console.log(data);

      const variables_enabled = {
        TMP: 'rgb(255, 99, 132)',
        CONDASNOW: 'rgb(54, 162, 235)',
      };
      let chartContainer = document.getElementById('charts_area');
      let chartData = {
        labels: Object.values(data[0]['forecast_timestamp']),
        datasets: [],
      };
      const canvasId = 'chart';

      for (let forecastVar of data) {
        if (!variables_enabled.hasOwnProperty(forecastVar['variable'][0])) {
          continue;
        }

        // let canvasId = 'chart_' + forecastVar['variable'][0];
        chartData['datasets'].push({
          label: forecastVar['variable_description'][0],
          data: Object.values(forecastVar['value']),
          borderColor: variables_enabled[forecastVar['variable'][0]],
          fill: false,
          cubicInterpolationMode: 'monotone',
          tension: 0.4,
          yAxisID: forecastVar['unit'][0],
        });

        if (canvasId in charts) {
          charts[canvasId].data.labels = chartData.labels;
          charts[canvasId].data.datasets = chartData.datasets;
          charts[canvasId].update();
        } else {
          let newCanvas = document.createElement('canvas');
          newCanvas.setAttribute('id', canvasId);
          chartContainer.appendChild(newCanvas);
          charts[canvasId] = drawChart(
            chartData,
            document.getElementById(canvasId)
          );
        }
      }
    })
    .catch(console.error);
}

export function drawChart(chartdata, canvasElement) {
  return new Chart(canvasElement, {
    type: 'line',
    data: chartdata,
    options: {
      responsive: true,
      aspectRatio: 1,
      plugins: {
        title: {
          display: true,
          text: '48 Hour forecast',
        },
        legend: {
          display: true,
        },
        annotation: {
          annotations: {
            line1: {
              type: 'line',
              yMin: 0,
              yMax: 0,
              borderColor: 'rgb(255, 99, 132)',
              borderWidth: 2,
            },
          },
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
              hour: 'h A, DD MMM ',
            },
            unit: 'hour',
            unitStepSize: 1,
          },
          axis: 'x',
          position: 'bottom',
        },
        C: {
          display: true,
          title: {
            display: true,
            text: 'Celsius',
          },
          position: 'left',
          type: 'linear',
          axis: 'y',
          min: -40,
          max: 40,
          grid: {
            drawOnChartArea: false,
            drawTicks: false,
          },
        },
        m: {
          display: true,
          title: {
            display: true,
            text: 'Meters',
          },
          position: 'right',
          axis: 'y',
          min: -1,
          max: 1,
          type: 'linear',
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
        getForecast(coords[0], coords[1]);
      }
    })
    .catch(console.error);
}
