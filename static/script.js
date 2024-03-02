
window.initMap = function() {
    console.log('initMap function called!');
    const map = new google.maps.Map(document.getElementById('googleMap'), {
        center: { lat: 37.7749, lng: -122.4194 },
        zoom: 12,
    });
};
       
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
        displayRoute(result.data.ev_optimal_route);
    })
    .catch(error => console.error('Error:', error));
}

function displayRoute(route) {
    const directionsService = new google.maps.DirectionsService();
    const directionsRenderer = new google.maps.DirectionsRenderer();
    
    directionsRenderer.setMap(map); // Assuming 'map' is your Google Map instance

    const request = {
        origin: route.start_location,
        destination: route.end_location,
        travelMode: 'DRIVING'
    };

    directionsService.route(request, function(response, status) {
        if (status === 'OK') {
            directionsRenderer.setDirections(response);
        } else {
            console.error('Directions request failed due to ' + status);
        }
    });
}



