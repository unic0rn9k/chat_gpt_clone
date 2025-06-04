document.getElementById('registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();
  
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();
    const passwordConfirm = document.getElementById('passwordConfirm').value.trim();
    const registerError = document.getElementById('registerError');
  
    registerError.textContent = '';
  
    if (!username || !password || !passwordConfirm) {
      registerError.textContent = 'Please fill out all fields.';
      return;
    }
  
    if (password !== passwordConfirm) {
      registerError.textContent = 'Passwords do not match.';
      return;
    }
  
    try {
      const response = await fetch('/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      });
  
      const data = await response.json();
  
      if (data.error) {
        registerError.textContent = data.error;
      } else {
        alert('Registration successful! You can now log in.');
        window.location.href = '/static/login.html';
      }
    } catch (error) {
      console.error('Registration error:', error);
      registerError.textContent = 'An error occurred. Please try again.';
    }
  });
  