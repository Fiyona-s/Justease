const body = document.body;
        
// this is for dark modes 
const themeIcon = document.getElementById('themeIcon');
const themeToggle = document.getElementById('themeToggle');
function toggleTheme() {
    document.body.classList.toggle("light_mode");
    
    console.log(localStorage.getItem("theme"));
    
    localStorage.setItem("theme", document.body.classList.contains("light_mode") ? "light" : "dark");
    
}

// Toggle User Dropdown
function toggleUserDropdown() {
    const dropdown = document.getElementById('userDropdown');
    dropdown.classList.toggle('hidden');
    dropdown.classList.toggle('active');
}

// Close Dropdown When Clicking Outside
document.addEventListener('click', (event) => {
    const dropdown = document.getElementById('userDropdown');
    const avatar = document.querySelector('.avatar');
    if (!avatar.contains(event.target) && !dropdown.contains(event.target)) {
        dropdown.classList.add('hidden');
        dropdown.classList.remove('active');
    }
});

// Logout Function
async function handleLogout() {
    try {
        const response = await fetch('/logout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
        });

        if (response.ok) {
            window.location.href = '/login'; // Redirect to login page
        } else {
            alert('Logout failed. Please try again.');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while logging out.');
    }
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
