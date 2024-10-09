function initMap() {
    // Ustawienie mapy na Kraków
    const krakow = { lat: 50.0647, lng: 19.9450 };

    // Inicjalizacja mapy
    const map = new google.maps.Map(document.getElementById("map"), {
        center: krakow, // Kraków jako domyślny punkt
        zoom: 12
    });

    // Marker dla domyślnego punktu
    const marker = new google.maps.Marker({
        position: krakow,
        map: map,
        title: "Kraków",
        draggable: true
    });

    // Aktualizacja inputa latlng na domyślne współrzędne
    document.getElementById("latlng").value = `${krakow.lat}, ${krakow.lng}`;

    // Reverse geocoding dla domyślnej lokalizacji
    reverseGeocode(krakow.lat, krakow.lng);

    // Listener na kliknięcia mapy
    map.addListener("click", (event) => {
        const clickedLocation = event.latLng;
        const lat = clickedLocation.lat();
        const lng = clickedLocation.lng();

        // Przesunięcie markera na kliknięte miejsce
        marker.setPosition(clickedLocation);

        // Aktualizacja inputa latlng
        document.getElementById("latlng").value = `${lat}, ${lng}`;

        // Reverse geocoding
        reverseGeocode(lat, lng);
    });

    // Listener na przeciąganie markera
    marker.addListener("dragend", () => {
        const position = marker.getPosition();
        const lat = position.lat();
        const lng = position.lng();

        // Aktualizacja inputa latlng
        document.getElementById("latlng").value = `${lat}, ${lng}`;

        // Reverse geocoding
        reverseGeocode(lat, lng);
    });
}

function reverseGeocode(lat, lng) {
    const geocoder = new google.maps.Geocoder();
    const latlng = { lat: lat, lng: lng };

    geocoder.geocode({ location: latlng }, (results, status) => {
        if (status === "OK") {
            if (results[0]) {
                const addressComponents = results[0].address_components;

                let street = "";
                let streetNumber = "";
                let city = "";
                let postalCode = "";
                let administrativeArea = "";

                // Rozdzielanie komponentów adresu
                addressComponents.forEach(component => {
                    const types = component.types;
                    if (types.includes("street_number")) {
                        streetNumber = component.long_name;
                    }
                    if (types.includes("route")) {
                        street = component.long_name;
                    }
                    if (types.includes("locality")) {
                        city = component.long_name;
                    }
                    if (types.includes("administrative_area_level_1")) {
                        administrativeArea = component.long_name;
                    }
                    if (types.includes("postal_code")) {
                        postalCode = component.long_name;
                    }
                });

                // Aktualizacja odpowiednich pól formularza
                document.getElementById("location-input").value = `${street} ${streetNumber}`;
                document.getElementById("locality-input").value = city;
                document.getElementById("administrative_area_level_1-input").value = administrativeArea;
                document.getElementById("postal_code-input").value = postalCode;
            } else {
                window.alert("Brak wyników dla podanej lokalizacji.");
                document.getElementById("location-input").value = "";
            }
        } else {
            window.alert("Geocoder nie mógł znaleźć lokalizacji: " + status);
            document.getElementById("location-input").value = "";
        }
    });
}
