function areas() {
    var inputValue = document.getElementById("liczba-swiadkow").value;
    var divek = document.getElementById("divek-witnesses");
    divek.innerHTML = ""; // Wyczyszczenie zawartości divek przed dodaniem nowych pól tekstowych

    for (var i = 1; i <= inputValue; i++) {
        var textarea = document.createElement('textarea');
        var br = document.createElement('br');
        textarea.setAttribute("placeholder", "Dane kontaktowe " + i + ". świadka...");
        textarea.setAttribute("id", "świadek" + i);
        textarea.setAttribute("name", "świadek" + i);
        textarea.classList.add('witness'); // Dodajemy klasę zamiast id
        divek.appendChild(textarea);
        divek.appendChild(br);
    }

}

// Wywołanie funkcji areas() przy zmianie wartości pola liczba
document.getElementById("liczba-swiadkow").addEventListener("input", areas);