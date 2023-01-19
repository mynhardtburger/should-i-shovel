import { getForecast } from './shouldishovel';
import './style.css';

function printMe() {
  console.log('I get called from print.js!');
}

function component() {
  const element = document.createElement('div');
  const btn = document.createElement('button');

  element.innerHTML = _.join(['Hello', 'webpack'], ' ');

  btn.innerHTML = 'Click me and check the console!';
  btn.onclick = printMe;

  element.appendChild(btn);

  return element;
}

// document.body.appendChild(component());

let map, infoWindow;
let markers = [];

function initMap() {
  map = new google.maps.Map(document.getElementById('map'), {
    center: { lat: 49.886061, lng: -97.126819 },
    zoom: 5,
  });
  infoWindow = new google.maps.InfoWindow();

  const locationButton = document.createElement('button');

  locationButton.textContent = 'Pan to Current Location';
  locationButton.classList.add('custom-map-control-button');
  map.controls[google.maps.ControlPosition.TOP_CENTER].push(locationButton);
  locationButton.addEventListener('click', () => {
    // Try HTML5 geolocation.
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const pos = {
            lat: position.coords.latitude,
            lng: position.coords.longitude,
          };

          map.setCenter(pos);
          addMarker(pos);
          getForecast(pos.lat, pos.lng);
        },
        () => {
          handleLocationError(true, infoWindow, map.getCenter());
        }
      );
    } else {
      // Browser doesn't support Geolocation
      handleLocationError(false, infoWindow, map.getCenter());
    }
  });

  map.addListener('click', (mapsMouseEvent) => {
    // map.setZoom(8);
    deleteMarkers();
    addMarker(mapsMouseEvent.latLng);
    map.panTo(mapsMouseEvent.latLng);
    console.log(mapsMouseEvent.latLng.toString());
    getForecast(mapsMouseEvent.latLng.lat(), mapsMouseEvent.latLng.lng());
  });
}

function addMarker(position) {
  const marker = new google.maps.Marker({
    position,
    map,
  });

  markers.push(marker);
}

function setMapOnAll(map) {
  for (let i = 0; i < markers.length; i++) {
    markers[i].setMap(map);
  }
}

function hideMarkers() {
  setMapOnAll(null);
}

function deleteMarkers() {
  hideMarkers();
  markers = [];
}

function handleLocationError(browserHasGeolocation, infoWindow, pos) {
  infoWindow.setPosition(pos);
  infoWindow.setContent(
    browserHasGeolocation
      ? 'Error: The Geolocation service failed.'
      : "Error: Your browser doesn't support geolocation."
  );
  infoWindow.open(map);
}

window.initMap = initMap;

// const button = document.getElementById('getData');
// const button_address = document.getElementById('getData_address');
// button.addEventListener('click', () =>
//   get_forecast(
//     document.getElementById('f_lat').value,
//     document.getElementById('f_lng').value
//   )
// );
// button_address.addEventListener('click', get_forecast_for_address);
