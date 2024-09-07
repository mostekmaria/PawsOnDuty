// Sidebar podstawie https://www.w3schools.com/howto/howto_css_fixed_sidebar.asp
function openNav() {
  document.getElementById("mySidebar").style.width = "320px";
  document.getElementById("main").style.marginRight = "320px";
}

function closeNav() {
  document.getElementById("mySidebar").style.width = "0";
  document.getElementById("main").style.marginRight= "0";
}
