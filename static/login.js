(async () => {
    const form = document.getElementById('loginForm');
    const errorEl = document.getElementById('loginError');
  
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      errorEl.textContent = ''; // Clear any previous error
  
      const username = form.username.value.trim();
      const password = form.password.value;
  
      // Basic front-end validation (can be expanded)
      if (!username || !password) {
        errorEl.textContent = 'Please enter both username and password.';
        return;
      }
  
      try {
        const response = await fetch('/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ username, password })
        });
  
        if (response.ok) {
          // Login succeeded; redirect to main page ("/" or wherever)
          window.location.href = '/';
        } else if (response.status === 401) {
          errorEl.textContent = 'Invalid username or password.';
        } else {
          // Other error (400, 500, etc.)
          errorEl.textContent = 'Login failed. Please try again.';
        }
      } catch (err) {
        console.error('Network or server error:', err);
        errorEl.textContent = 'Cannot connect to server.';
      }
    });
  })();
  