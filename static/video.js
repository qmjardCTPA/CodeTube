document.addEventListener('DOMContentLoaded', () => {
  const postBtn = document.getElementById('postComment');
  const commentText = document.getElementById('commentText');
  const commentsList = document.getElementById('commentsList');
  if (postBtn) {
    const segments = window.location.pathname.split('/');
    const videoId = segments[segments.length - 1];

    postBtn.addEventListener('click', async () => {
      const text = commentText.value.trim();
      if (!text) return;
      postBtn.disabled = true;
      try {
        const res = await fetch(`/api/video/${videoId}/comment`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text })
        });
        const data = await res.json();
        if (res.status === 201 && data.comment) {
          const li = document.createElement('li');
          li.className = 'comment';
          li.innerHTML = `<div class="comment-author">${data.comment.author}</div>
                          <div class="comment-text">${data.comment.text}</div>
                          <div class="comment-date">${data.comment.created_at}</div>`;
          commentsList.prepend(li);
          commentText.value = '';
        } else {
          alert(data.error || 'Error al publicar comentario');
        }
      } catch (err) {
        alert('Error de red');
      } finally {
        postBtn.disabled = false;
      }
    });
  }

  const deleteBtn = document.getElementById('deleteVideoBtn');
  if (deleteBtn) {
    const segments = window.location.pathname.split('/');
    const videoId = segments[segments.length - 1];
    deleteBtn.addEventListener('click', async () => {
      if (!confirm('Eliminar este video? Esta acción no se puede deshacer.')) return;
      deleteBtn.disabled = true;
      try {
        const res = await fetch(`/api/video/${videoId}`, { method: 'DELETE' });
        const data = await res.json();
        if (res.ok) {
          window.location.href = '/library';
        } else {
          alert(data.error || 'Error al eliminar el video');
        }
      } catch (err) {
        alert('Error de red');
      } finally {
        deleteBtn.disabled = false;
      }
    });
  }
});