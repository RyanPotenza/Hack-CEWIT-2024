// Global vars
let map
let directionsRenderer
let directionsService
let transportMethod = 'ev'

function initMap() {
    directionsService = new google.maps.DirectionsService();
    directionsRenderer = new google.maps.DirectionsRenderer();

    map = new google.maps.Map(document.getElementById('googleMap'), {
        center: { lat: 40.7588, lng: -73.9851 },
        zoom: 12,
    });
    directionsRenderer.setMap(map);

    return map;
};

function toggleTransport() {
    const transportMethod = document.getElementById('transportMode').value;

    if (transportMethod == 'ev')
        sendData();
    else if (transportMethod == 'transit')
        displayTransitRoute()
    else
        displayGasRoute()
}

function sendData() {
    // Get input values
    const batteryCapacity = document.getElementById('batteryCapacity').value;
    const startLocation = document.getElementById('startLocation').value;
    const destinationLocation = document.getElementById('destinationLocation').value;

    // Create a JSON object with the input data
    const data = {
        ev_battery_capacity: batteryCapacity,
        starting_location: startLocation,
        destination_location: destinationLocation
    };

    // Send a POST request to the backend
    fetch('http://127.0.0.1:5000/evroute', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        // Display the result in the frontend
        document.getElementById('evEmissions').textContent = `EV Emissions: ${result.data.ev_emissions}`;
        document.getElementById('gasEmissions').textContent = `Gas Emissions: ${result.data.gas_emissions}`;
        document.getElementById('publicEmissions').textContent = `Public Emissions: ${result.data.public_emissions}`;

        // Add code to display driving route on the map
        displayEVRoute(result.data);
    })
    .catch(error => console.error('Error:', error));
}

function displayEVRoute(data) {
    const request = {
        origin: data.start_location,
        destination: data.end_location, 
        travelMode: 'DRIVING',
        waypoints: data.waypoints,
    };

    directionsService.route(request, function(response, status) {
        if (status === 'OK') {
            directionsRenderer.setDirections(response);

            // Set Navigation time
            const route = response.routes[0];
            const navigationTimeInSeconds = route.legs.reduce((total, leg) => total + leg.duration.value, 0);
            const navigationTimeInMinutes = Math.round(navigationTimeInSeconds / 60);
            document.getElementById('navigationTime').textContent = `Navigation Time: ${navigationTimeInMinutes} minutes`;
        } else {
            console.error('Directions request failed due to ' + status);
        }
    });
}

function displayTransitRoute() {
    const request = {
        origin: document.getElementById('startLocation').value,
        destination: document.getElementById('destinationLocation').value,
        travelMode: 'TRANSIT',
    };

    directionsService.route(request, function(response, status) {
        if (status === 'OK') {
            directionsRenderer.setDirections(response);

            // Set Navigation time
            const navigationTime = response.routes[0].legs.reduce((total, leg) => total + leg.duration.value, 0);
            document.getElementById('navigationTime').textContent = `Navigation Time: ${formatTime(navigationTime)}`;
        } else {
            console.error('Directions request failed due to ' + status);
        }
    });
}

function displayGasRoute() {
    const request = {
        origin: document.getElementById('startLocation').value,
        destination: document.getElementById('destinationLocation').value,
        travelMode: 'DRIVING',
    };

    directionsService.route(request, function(response, status) {
        if (status === 'OK') {
            directionsRenderer.setDirections(response);

            // Set Navigation time
            const navigationTime = response.routes[0].legs.reduce((total, leg) => total + leg.duration.value, 0);
            document.getElementById('navigationTime').textContent = `Navigation Time: ${formatTime(navigationTime)}`;
        } else {
            console.error('Directions request failed due to ' + status);
        }
    });
}



