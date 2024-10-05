function initMap() {
  const initialLocation = { lat: 40.714224, lng: -73.961452 }; // Ustawienie lokalizacji startowej
  const map = new google.maps.Map(document.getElementById("map"), { // Zmień 'map' na odpowiedni ID
      zoom: 12,
      center: initialLocation,
  });

  const marker = new google.maps.Marker({
      position: initialLocation,
      map: map,
      title: "Wybierz miejsce!",
      draggable: true, // Marker jest przeciągalny
  });

  // Dodanie listenera do klikania na mapie
  map.addListener("click", (event) => {
      const latLng = event.latLng;
      const lat = latLng.lat();
      const lng = latLng.lng();
      // Wywołanie reverse geocoding
      reverseGeocode(lat, lng);
  });
}

function reverseGeocode(lat, lng) {
  const geocoder = new google.maps.Geocoder();
  const latlng = { lat: lat, lng: lng };

  geocoder.geocode({ location: latlng }, (results, status) => {
      if (status === "OK") {
          if (results[0]) {
              document.getElementById("location-input").value = results[0].formatted_address; // Wypełnij adres w polu
          } else {
              window.alert("Brak wyników dla podanej lokalizacji.");
          }
      } else {
          window.alert("Geocoder nie mógł znaleźć lokalizacji: " + status);
      }
  });
}