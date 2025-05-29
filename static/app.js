// Function to send message to the API and display response
async function sendMessage() {
    const userMessage = document.getElementById("userMessage").value;
    if (!userMessage) return; // Don't send empty messages

    // Display user message
    displayMessage(userMessage, 'user');

    // Call the API to get the response
    try {
        const response = await fetch(`/chat/${encodeURIComponent(userMessage)}`);
        const data = await response.json();

        // Display bot reply
        if (data && data.text) {
            displayMessage(data.text, 'bot');
        } else {
            displayMessage("Sorry, I couldn't get a response.", 'bot');
        }
    } catch (error) {
        console.error('Error:', error);
        displayMessage("Error connecting to the server.", 'bot');
    }

    // Clear the input field
    document.getElementById("userMessage").value = '';
}

// Function to display message in chat box
function displayMessage(message, sender) {
    const chatBox = document.getElementById("chatBox");
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', `${sender}-message`);
    messageDiv.textContent = message;

    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight; // Scroll to the latest message
}
