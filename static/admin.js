document.addEventListener('DOMContentLoaded', () => {
  // Helper
  async function req(url, opts) {
    const res = await fetch(url, opts);
    const data = await res.json().catch(()=>({}));
    if (!res.ok) throw data;
    return data;
  }

  // Usuarios: cambiar rol
  document.querySelectorAll('#usersTable .btn-role').forEach(btn => {
    btn.addEventListener('click', async () => {
      const tr = btn.closest('tr');
      const id = tr.dataset.id;
      const newRole = btn.dataset.role;
      if (!confirm(`Cambiar rol a "${newRole}" para ${tr.children[0].textContent}?`)) return;
      try {
        await req(`/api/user/${id}/role`, { method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ role: newRole }) });
        tr.querySelector('.role').textContent = newRole;
        btn.textContent = newRole === 'admin' ? 'Degradar' : 'Promover';
        btn.dataset.role = newRole === 'admin' ? 'user' : 'admin';
      } catch (err) {
        alert(err.error || 'Error cambiando rol');
      }
    });
  });

  // Usuarios: eliminar
  document.querySelectorAll('#usersTable .btn-delete-user').forEach(btn => {
    btn.addEventListener('click', async () => {
      const tr = btn.closest('tr');
      const id = tr.dataset.id;
      if (!confirm('Eliminar usuario y todos sus videos/comentarios?')) return;
      try {
        await req(`/api/user/${id}`, { method: 'DELETE' });
        tr.remove();
      } catch (err) {
        alert(err.error || 'Error eliminando usuario');
      }
    });
  });

  // Videos: eliminar
  document.querySelectorAll('#videosTable .btn-delete-video').forEach(btn => {
    btn.addEventListener('click', async () => {
      const tr = btn.closest('tr');
      const id = tr.dataset.id;
      if (!confirm('Eliminar video permanentemente?')) return;
      try {
        await req(`/api/video/${id}`, { method: 'DELETE' });
        tr.remove();
      } catch (err) {
        alert(err.error || 'Error eliminando video');
      }
    });
  });

  // Comentarios: eliminar
  document.querySelectorAll('#commentsTable .btn-delete-comment').forEach(btn => {
    btn.addEventListener('click', async () => {
      const tr = btn.closest('tr');
      const id = tr.dataset.id;
      if (!confirm('Eliminar comentario?')) return;
      try {
        await req(`/api/comment/${id}`, { method: 'DELETE' });
        tr.remove();
      } catch (err) {
        alert(err.error || 'Error eliminando comentario');
      }
    });
  });
});