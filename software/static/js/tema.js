(function () {
  const CLAVE = 'tema-hidrico';
  function aplicar(t) {
    document.documentElement.setAttribute('data-tema', t);
    const b = document.getElementById('btn-tema');
    if (b) b.textContent = t === 'claro' ? '☾ Oscuro' : '☀ Claro';
  }
  let t = 'oscuro';
  try { t = localStorage.getItem(CLAVE) || 'oscuro'; } catch (e) {}
  aplicar(t);
  document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('btn-tema').addEventListener('click', function () {
      t = document.documentElement.getAttribute('data-tema') === 'claro' ? 'oscuro' : 'claro';
      try { localStorage.setItem(CLAVE, t); } catch (e) {}
      aplicar(t);
    });
  });
})();
