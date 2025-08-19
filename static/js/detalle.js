// static/js/detalle.js
(function () {
  // =========================
  // GALERÍA + LIGHTBOX
  // =========================
  const main = document.getElementById('mainImageDisplay');
  const thumbsGrid = document.getElementById('thumbsGrid');

  const lb = document.getElementById('imageLightbox');
  const lbImg = document.getElementById('lb-img');
  const lbPrev = document.getElementById('lb-prev');
  const lbNext = document.getElementById('lb-next');
  const lbClose = document.getElementById('lb-close');
  const lbBackdrop = document.getElementById('imageLightboxBackdrop');

  try {
    if (main) {
      const gallery = [];
      const pushUnique = (src) => { if (src && !gallery.includes(src)) gallery.push(src); };

      // Construir galería con la imagen principal y miniaturas
      pushUnique(main.currentSrc || main.src);
      if (thumbsGrid) {
        thumbsGrid.querySelectorAll('img').forEach(img => {
          pushUnique(img.currentSrc || img.src);
        });
      }

      let current = 0;

      function highlightActive(src) {
        if (!thumbsGrid) return;
        thumbsGrid.querySelectorAll('img').forEach(t => t.classList.remove('ring-2', 'ring-blue-500'));
        const active = Array.from(thumbsGrid.querySelectorAll('img')).find(
          t => (t.currentSrc || t.src) === src
        );
        if (active) active.classList.add('ring-2', 'ring-blue-500');
      }

      function setMain(i) {
        if (!gallery.length) return;
        current = (i % gallery.length + gallery.length) % gallery.length;
        const src = gallery[current];
        main.src = src;
        highlightActive(src);
      }

      // Click en miniaturas
      if (thumbsGrid) {
        thumbsGrid.querySelectorAll('img').forEach(img => {
          img.addEventListener('click', () => {
            const src = img.currentSrc || img.src;
            const idx = gallery.indexOf(src);
            setMain(idx >= 0 ? idx : 0);
          });
        });
      }

      // LIGHTBOX
      function openLB(i) {
        setMain(i ?? current);
        lbImg.src = gallery[current];
        lb.classList.remove('hidden');
        lb.classList.add('flex');
        document.body.style.overflow = 'hidden';
      }
      function closeLB() {
        lb.classList.add('hidden');
        lb.classList.remove('flex');
        document.body.style.overflow = '';
      }
      function next() { setMain(current + 1); lbImg.src = gallery[current]; }
      function prev() { setMain(current - 1); lbImg.src = gallery[current]; }

      main.addEventListener('click', () => openLB(current));
      main.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') openLB(current); });

      if (lbNext) lbNext.addEventListener('click', next);
      if (lbPrev) lbPrev.addEventListener('click', prev);
      if (lbClose) lbClose.addEventListener('click', closeLB);
      if (lbBackdrop) lbBackdrop.addEventListener('click', closeLB);

      document.addEventListener('keydown', (e) => {
        if (!lb || lb.classList.contains('hidden')) return;
        if (e.key === 'Escape') closeLB();
        if (e.key === 'ArrowRight') next();
        if (e.key === 'ArrowLeft') prev();
      });

      // Resaltar la actual al cargar
      highlightActive(main.currentSrc || main.src);
    }
  } catch (err) {
    console.error('Galería/Lightbox error:', err);
  }

  // =========================
  // MAPA (por dirección)
  // =========================
  try {
    const box = document.querySelector('.map-frame[data-address]');
    if (!box) return;

    const iframe = box.querySelector('iframe');
    if (!iframe) return;

    const address = (box.dataset.address || '').replace(/\s+/g, ' ').trim();
    if (!address) return;

    // Google Maps embed por búsqueda de dirección (muestra marcador en la mayoría de los casos)
    const url = 'https://www.google.com/maps?output=embed&z=15&q=' + encodeURIComponent(address);
    iframe.src = url;
  } catch (err) {
    console.error('Mapa error:', err);
  }
})();
