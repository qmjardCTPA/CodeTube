
document.addEventListener('DOMContentLoaded', () => {
  const editorContainer = document.getElementById('jsEditor');
  if (!editorContainer) return;

  let initial = '';
  try { initial = JSON.parse(editorContainer.getAttribute('data-code') || '""') || ''; } catch (e) { initial = ''; }

  const editor = (window.ace) ? ace.edit('jsEditor') : null;
  if (editor) {
    editor.setTheme('ace/theme/monokai');
    editor.session.setMode('ace/mode/javascript');
    editor.session.setUseWrapMode(true);
    editor.setValue(initial, -1);
    editor.setOptions({ fontSize: '13px', showPrintMargin: false });
  } else {
    const ta = document.createElement('textarea');
    ta.id = 'jsEditorFallback';
    ta.style.width = '100%';
    ta.style.height = '260px';
    ta.value = initial;
    editorContainer.replaceWith(ta);
  }

  const runBtn = document.getElementById('runCodeBtn');
  const stopBtn = document.getElementById('stopCodeBtn');
  const clearBtn = document.getElementById('clearOutputBtn');
  const saveBtn = document.getElementById('saveCodeBtn');
  const outputEl = document.getElementById('editorOutput');

  let runnerFrame = null;

  function appendOutput(text, cls = '') {
    const p = document.createElement('pre');
    p.textContent = text;
    p.className = cls;
    outputEl.appendChild(p);
    outputEl.scrollTop = outputEl.scrollHeight;
  }

  function createRunnerIframe() {
    if (runnerFrame) {
      runnerFrame.remove();
      runnerFrame = null;
    }
    runnerFrame = document.createElement('iframe');
    runnerFrame.style.display = 'none';
    runnerFrame.setAttribute('sandbox', 'allow-scripts');
    const src = `<!doctype html><html><head><meta charset="utf-8"></head><body>
      <script>
        (function(){
          function send(type, msg){ parent.postMessage({type: type, msg: String(msg)}, '*'); }
          console.log = function(){ send('log', Array.from(arguments).map(String).join(' ')); };
          console.error = function(){ send('error', Array.from(arguments).map(String).join(' ')); };
          window.onerror = function(msg, src, line){ send('error', msg + ' (línea ' + line + ')'); };
          window.addEventListener('message', function(e){
            try {
              var code = e.data && e.data.code ? e.data.code : '';
              (new Function(code))();
              send('done', 'Ejecución finalizada');
            } catch (err) {
              send('error', err && err.message ? err.message : String(err));
            }
          }, false);
          send('ready', 'sandbox listo');
        })();
      <\/script>
      </body></html>`;
    runnerFrame.srcdoc = src;
    document.body.appendChild(runnerFrame);
  }

  // listen messages from iframe
  window.addEventListener('message', (e) => {
    // ensure source is our iframe
    if (!runnerFrame || e.source !== runnerFrame.contentWindow) return;
    const data = e.data || {};
    if (data.type === 'log') appendOutput(data.msg, 'out-log');
    else if (data.type === 'error') appendOutput('Error: ' + data.msg, 'out-err');
    else if (data.type === 'done') appendOutput(data.msg, 'out-done');
    else if (data.type === 'ready') appendOutput('Sandbox listo', 'out-info');
  });

  runBtn.addEventListener('click', () => {
    // clear old outputs
    appendOutput('--- Ejecutando ---', 'out-info');
    createRunnerIframe();
    // wait a short moment to ensure iframe loads
    setTimeout(() => {
      const code = editor ? editor.getValue() : document.getElementById('jsEditorFallback').value;
      try {
        runnerFrame.contentWindow.postMessage({ code }, '*');
      } catch (err) {
        appendOutput('No se pudo enviar código al sandbox', 'out-err');
      }
    }, 150);
  });

  stopBtn.addEventListener('click', () => {
    if (runnerFrame) {
      runnerFrame.remove();
      runnerFrame = null;
      appendOutput('Proceso detenido', 'out-info');
    } else {
      appendOutput('No hay proceso corriendo', 'out-info');
    }
  });

  clearBtn.addEventListener('click', () => { outputEl.innerHTML = ''; });

  if (saveBtn) {
    saveBtn.addEventListener('click', async () => {
      saveBtn.disabled = true;
      const code = editor ? editor.getValue() : document.getElementById('jsEditorFallback').value;
      const segments = window.location.pathname.split('/');
      const videoId = segments[segments.length - 1];
      try {
        const res = await fetch(`/api/video/${videoId}/code`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code })
        });
        const data = await res.json();
        if (!res.ok) appendOutput('Error guardando: ' + (data.error || JSON.stringify(data)), 'out-err');
        else appendOutput('Código guardado', 'out-info');
      } catch (err) {
        appendOutput('Error de red', 'out-err');
      } finally {
        saveBtn.disabled = false;
      }
    });
  }
});