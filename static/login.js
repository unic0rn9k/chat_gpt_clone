document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
  
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
  
    try {
      const response = await fetch('/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });
  
      const data = await response.json();
  
      if (response.ok && data.success) {
        // Success: redirect or show message
        window.location.href = '/';
      } else {
        // Failure: show error
        document.getElementById('loginError').textContent = '❌ ' + data.message;
      }
    } catch (err) {
      document.getElementById('loginError').textContent = '⚠️ Network error';
    }
  });
  
  