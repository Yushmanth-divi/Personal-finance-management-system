function openModal() {
    document.getElementById('modal-overlay').style.display = 'block';
    document.getElementById('add-account-modal').style.display = 'block';
}

function closeModal() {
    document.getElementById('modal-overlay').style.display = 'none';
    document.getElementById('add-account-modal').style.display = 'none';
}

document.querySelector("form").addEventListener("submit", function (event) {
    event.preventDefault(); 
    var form = event.target;
    var formData = new FormData(form);

    fetch("/add_account", {
        method: "POST",
        body: formData
    })
    .then(response => response.text())  
    .then(data => {
        window.location.reload();
    })
    .catch(error => console.error("Error:", error));
});
