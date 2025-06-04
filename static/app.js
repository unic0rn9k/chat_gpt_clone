// Function to send message to the API and display response
function simpleMarkdownParser(text) {
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');   // bold
    text = text.replace(/\*(.+?)\*/g, '<em>$1</em>');               // italic
    text = text.replace(/`(.+?)`/g, '<code>$1</code>');             // inline code
    text = text.replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2">$1</a>'); // links
    text = text.replace(/\n/g, '<br>');                             // new lines to <br>
    return text;
  }

async function sendMessage() {
    const userMessage = document.getElementById("userMessage").value;
    if (!userMessage) return; // Don't send empty messages

    // Display user message
    displayMessage(userMessage, 'user');

    // Call the API to get the response
    try {
        const response = await fetch(`/chat/${encodeURIComponent(userMessage)}`);
        const data = await response.json();
        const parsedText = simpleMarkdownParser(data.text);

        // Display bot reply
        if (data && data.text) {
            displayMessage(parsedText, 'bot');
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
    messageDiv.innerHTML = message;

    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight; // Scroll to the latest message
}
