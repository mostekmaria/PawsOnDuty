// Sidebar podstawie https://www.w3schools.com/howto/howto_css_fixed_sidebar.asp
function openCloseNav() {
  const sidebar = document.getElementById("mySidebar");
    
  // Jeśli sidebar jest otwarty (ma szerokość 250px), zamknij go
  if (sidebar.style.width === "290px") {
      sidebar.style.width = "0";
  } else {
      // W przeciwnym razie otwórz sidebar
      sidebar.style.width = "290px";
  }
}


window.addEventListener("resize", function() {
  const sidebar = document.getElementById("mySidebar");
  if (window.innerWidth > 1100) {
      sidebar.style.width = "0"; // Sidebar znika, gdy ekran jest większy
  }
});
