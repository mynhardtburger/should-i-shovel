function logSubmit() {
    window.alert("sometext");
}

function request_forecast(lat, lon) {
    lat = document.getElementById("f_lat").value
    lon = document.getElementById("f_lon").value
    res = fetch(`http://127.0.0.1:8000/forecast/?latitude=${lat}&longitude=${lon}`)
    console.log(res)
}

const form = document.getElementById('lat_lon_form');
form.addEventListener('submit', request_forecast());