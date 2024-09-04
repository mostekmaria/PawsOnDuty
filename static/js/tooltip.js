// Pobierz elementy
var tooltip = document.querySelector('.tooltip');
var targetElements = document.querySelectorAll('.has-tooltip');
var timeout;

// Dodaj obsługę zdarzeń dla elementów docelowych
targetElements.forEach(function(element) {
  element.addEventListener('mousemove', function(event) {
    // Zresetuj timeout, aby anulować poprzednią opóźnioną akcję tooltipu
    clearTimeout(timeout);

    // Pobierz tekst tooltipa z atrybutu danych
    var tooltipText = element.getAttribute('data-tooltip');

    // Ustaw timeout, aby pokazać tooltip po opóźnieniu
    timeout = setTimeout(function() {
      // Pobierz pozycję kursora
      var x = event.clientX + 12;
      var y = event.clientY + 16;

      // Ustaw pozycję i tekst tooltipa
      tooltip.style.display = 'block';
      tooltip.style.left = x + 'px';
      tooltip.style.top = y + 'px';
      tooltip.textContent = tooltipText;
    }, 200); 

  });

  element.addEventListener('mouseout', function() {
    // Ukryj tooltip, gdy kursor opuści element
    clearTimeout(timeout);
    tooltip.style.display = 'none';
  });
});