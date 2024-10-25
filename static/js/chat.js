document.addEventListener('DOMContentLoaded', function() {
    const sendBtn = document.getElementById('send');  // Nowy identyfikator przycisku
    const chatInput = document.getElementById('message-user');  // Nowy identyfikator pola tekstowego
    const chatBox = document.getElementsByClassName('chatbox');  // Nowy identyfikator kontenera czatu


    sendBtn.addEventListener('click', function() {
        const userInput = chatInput.value.trim();
        if (!userInput) return;  // Nie wysyłaj pustej wiadomości

        // Dodaj wiadomość użytkownika
        const userMessage = document.createElement('p');
        userMessage.classList.add('message', 'user');
        userMessage.textContent = userInput;
        chatBox.appendChild(userMessage);

        // Przewiń czat na dół
        chatBox.scrollTop = chatBox.scrollHeight;

        // Wyczyść pole tekstowe
        chatInput.value = "";
    });
});
