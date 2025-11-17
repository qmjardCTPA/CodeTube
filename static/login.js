// ...new file...
document.addEventListener('DOMContentLoaded', () => {
  function show(el, msg) {
    if (!el) return;
    el.textContent = msg;
    el.classList.add('show');
    clearTimeout(el._hideTimer);
    el._hideTimer = setTimeout(() => {
      el.classList.remove('show');
    }, 4000);
  }

  const registerForm = document.getElementById('registerForm');
  const loginForm = document.getElementById('loginForm');
  const registerError = document.getElementById('errorMessage');
  const registerSuccess = document.getElementById('successMessage');

  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const username = document.getElementById('username').value.trim();
      const email = document.getElementById('email').value.trim();
      const password = document.getElementById('password').value;

      try {
        const res = await fetch('/api/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, email, password })
        });
        const data = await res.json();
        if (res.status === 201) {
          show(registerSuccess, data.message || 'Registro exitoso');
          setTimeout(() => { window.location.href = '/login'; }, 1300);
        } else {
          show(registerError, data.error || 'Error en el registro');
        }
      } catch (err) {
        show(registerError, 'Error de red. Intenta de nuevo.');
      }
    });
  }

  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const username = document.getElementById('username').value.trim();
      const password = document.getElementById('password').value;

      try {
        const res = await fetch('/api/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (res.status === 200) {
          show(registerSuccess, data.message || 'Inicio de sesión exitoso');
          setTimeout(() => { window.location.href = '/'; }, 800);
        } else {
          show(registerError, data.error || 'Usuario o contraseña incorrectos');
        }
      } catch (err) {
        show(registerError, 'Error de red. Intenta de nuevo.');
      }
    });
  }
});