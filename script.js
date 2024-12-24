function showRegister() {
    document.getElementById('login-form').classList.remove('active');
    document.getElementById('register-form').classList.add('active');
}


function showLogin() {
    document.getElementById('register-form').classList.remove('active');
    document.getElementById('login-form').classList.add('active');
}

function authenticateLogin(event) {
    event.preventDefault();


    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;


    const storedEmail = localStorage.getItem('email');
    const storedPassword = localStorage.getItem('password');


    if (email === storedEmail && password === storedPassword) {
        window.location.href = 'home.html';
    } else {
        alert('Invalid email or password');
    }
}


function registerUser(event) {
    event.preventDefault();


    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;


    localStorage.setItem('username', username);
    localStorage.setItem('email', email);
    localStorage.setItem('password', password);

    alert('Registration successful');
    showLogin();
}
