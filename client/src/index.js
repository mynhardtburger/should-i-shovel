import { drawChart, getForecast } from './shouldishovel';
import './style.css';

let map, infoWindow, mychart;
let markers = [];

function initMap() {
  map = new google.maps.Map(document.getElementById('map'), {
    center: { lat: 49.886061, lng: -97.126819 },
    zoom: 5,
  });
  infoWindow = new google.maps.InfoWindow();
  function panToGeoLocation() {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const pos = {
            lat: position.coords.latitude,
            lng: position.coords.longitude,
          };

          map.panTo(pos);
          map.setZoom(10);
          addMarker(pos);
          getForecast(pos.lat, pos.lng, mychart);
        },
        () => {
          handleLocationError(true, infoWindow, map.getCenter());
        }
      );
    } else {
      // Browser doesn't support Geolocation
      handleLocationError(false, infoWindow, map.getCenter());
    }
  }

  panToGeoLocation();

  const locationButton = document.createElement('button');
  locationButton.textContent = 'Pan to Current Location';
  locationButton.classList.add('custom-map-control-button');
  map.controls[google.maps.ControlPosition.TOP_CENTER].push(locationButton);

  locationButton.addEventListener('click', () => {
    panToGeoLocation();
  });

  map.addListener('click', (mapsMouseEvent) => {
    deleteMarkers();
    addMarker(mapsMouseEvent.latLng);
    map.panTo(mapsMouseEvent.latLng);
    console.log(mapsMouseEvent.latLng.toString());
    getForecast(
      mapsMouseEvent.latLng.lat(),
      mapsMouseEvent.latLng.lng(),
      mychart
    );
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
mychart = drawChart();
