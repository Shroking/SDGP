document.getElementById('upload-form').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the default form submission behavior

    const formData = new FormData(this);

    fetch('/submit-your-data', {  // Replace with your server's upload URL
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        const messageDiv = document.getElementById('message');
        if (data.success) {
            messageDiv.textContent = "File uploaded successfully!";
            messageDiv.classList.add('success');
            messageDiv.classList.remove('error');
        } else {
            messageDiv.textContent = "Error uploading file.";
            messageDiv.classList.add('error');
            messageDiv.classList.remove('success');
        }
    })
    .catch(error => {
        const messageDiv = document.getElementById('message');
        messageDiv.textContent = "Error uploading file.";
        messageDiv.classList.add('error');
        messageDiv.classList.remove('success');
    });
});
