const body = document.body;
        
// this is for dark modes 
const themeIcon = document.getElementById('themeIcon');
const themeToggle = document.getElementById('themeToggle');
function toggleTheme() {
    document.body.classList.toggle("light_mode");
    
    console.log(localStorage.getItem("theme"));
    
    localStorage.setItem("theme", document.body.classList.contains("light_mode") ? "light" : "dark");
    
}
// this function is to check if the data in localstorage is light or dark
function initialize() {
    // Load saved theme
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "light") {
        document.body.classList.add("light_mode");
    }
}
initialize();w
themeToggle.addEventListener('click', toggleTheme)