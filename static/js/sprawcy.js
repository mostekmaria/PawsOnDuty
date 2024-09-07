 function areas() {
    var inputValue = document.getElementById("liczba").value;
    var divek = document.getElementById("divek");
    divek.innerHTML = ""; // Wyczyszczenie zawartości divek przed dodaniem nowych pól tekstowych

    for (var i = 1; i <= inputValue; i++) {
        var textarea = document.createElement('textarea');
        var br = document.createElement('br');
        textarea.setAttribute("placeholder", "W tym miejscu opisz " + i + ". sprawcę...");
        textarea.setAttribute("id", "sprawca" + i);
        textarea.setAttribute("name", "sprawca" + i);
        divek.appendChild(textarea);
        divek.appendChild(br);
    }
}

// Wywołanie funkcji areas() przy zmianie wartości pola liczba
document.getElementById("liczba").addEventListener("input", areas);