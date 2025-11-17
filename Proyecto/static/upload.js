document.getElementById('uploadForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const title = document.getElementById('title').value;
  const description = document.getElementById('description').value;
  const file = document.getElementById('file').files[0];
  
  if (!file) {
    alert('Selecciona un archivo');
    return;
  }
  
  const formData = new FormData();
  formData.append('title', title);
  formData.append('description', description);
  formData.append('file', file);
  
  try {
    const response = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });
    
    const data = await response.json();
    
    if (response.status === 201) {
      document.getElementById('successMessage').textContent = data.message;
      document.getElementById('successMessage').classList.add('show');
      setTimeout(() => window.location.href = '/', 2000);
    } else {
      document.getElementById('errorMessage').textContent = data.error;
      document.getElementById('errorMessage').classList.add('show');
    }
  } catch (err) {
    document.getElementById('errorMessage').textContent = 'Error al subir';
    document.getElementById('errorMessage').classList.add('show');
  }
});