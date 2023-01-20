import Chart from 'chart.js/auto';
import 'chartjs-adapter-moment';
import _ from 'lodash';
import annotationPlugin from 'chartjs-plugin-annotation';

Chart.register(annotationPlugin);

export const CHART_COLORS = {
  red: 'rgb(255, 99, 132)',
  orange: 'rgb(255, 159, 64)',
  yellow: 'rgb(255, 205, 86)',
  green: 'rgb(75, 192, 192)',
  blue: 'rgb(54, 162, 235)',
  purple: 'rgb(153, 102, 255)',
  grey: 'rgb(201, 203, 207)',
};

const axisMax = 400;

export function getForecast(lat, lng, chart) {
  fetch(
    `http://127.0.0.1:8000/forecast/coordinates?latitude=${lat}&longitude=${lng}`
  )
    .then((response) => response.json())
    .then((data) => {
      console.log(data);

      const variables_enabled = {
        C: { color: CHART_COLORS.red, label: 'Temperature', axis: 'C' },
        mm: {
          color: CHART_COLORS.blue,
          label: 'Snow Fall per Hour',
          axis: 'mm',
        },
        estimated_snow_height: {
          color: CHART_COLORS.purple,
          label: 'Cumulative Snow Depth',
          axis: 'mm',
        },
      };

      let chartData = {
        labels: Object.values(data['data']['forecast_timestamp']),
        datasets: [],
      };

      for (const variable of Object.keys(variables_enabled)) {
        chartData['datasets'].push({
          type: 'line',
          label: variables_enabled[variable].label,
          data: Object.values(data['data'][variable]),
          borderColor: variables_enabled[variable].color,
          fill: false,
          cubicInterpolationMode: 'monotone',
          tension: 0.4,
          yAxisID: variables_enabled[variable].axis,
        });
      }
      chartData['datasets'].push({
        type: 'bar',
        label: 'Shoveltime',
        data: Object.values(data['data']['shovel_time']).map((x) =>
          x ? 1 : undefined
        ),
        borderColor: 'rgba(255, 159, 64, 0.0)',
        backgroundColor: 'rgba(255, 159, 64, 0.5)',
        yAxisID: 'shoveltime',
      });

      chart.data['labels'] = chartData.labels;
      chart.data['datasets'] = chartData.datasets;
      chart.update();
    })
    .catch(console.error);
}

export function drawChart() {
  return new Chart(document.getElementById('canvas'), {
    type: 'line',
    data: {
      labels: [],
      datasets: [],
    },
    options: {
      responsive: true,
      aspectRatio: 1,
      datasets: {
        bar: {
          barPercentage: 1,
          categoryPercentage: 0.9999,
        },
      },
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
            display: false,
          },
        },
        mm: {
          display: true,
          title: {
            display: true,
            text: 'Millimeter',
          },
          position: 'right',
          axis: 'y',
          min: -axisMax,
          max: axisMax,
          type: 'linear',
        },
        shoveltime: {
          min: 0,
          max: 1,
          axis: 'y',
          title: {
            display: false,
          },
          grid: {
            display: false,
          },
          display: false,
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
