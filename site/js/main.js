/* ============================================================================
   RecallOS Landing Page — main.js
   Scroll animations, sticky nav, hamburger, back-to-top, copy-to-clipboard
   ============================================================================ */

(function () {
  'use strict';

  /* ---- DOM refs --------------------------------------------------------- */
  const nav         = document.querySelector('.site-nav');
  const hamburger   = document.querySelector('.hamburger');
  const navLinks    = document.querySelector('.nav-links');
  const backToTop   = document.querySelector('.back-to-top');
  const pipCopyBtns = document.querySelectorAll('.pip-copy');
  const fadeEls     = document.querySelectorAll('.fade-up');
  const sections    = document.querySelectorAll('section[id]');
  const navAnchors  = document.querySelectorAll('.nav-links a[href^="#"]');

  /* ---- Sticky nav on scroll --------------------------------------------- */
  function handleNavScroll() {
    if (!nav) return;
    if (window.scrollY > 60) {
      nav.classList.add('scrolled');
    } else {
      nav.classList.remove('scrolled');
    }
  }
  window.addEventListener('scroll', handleNavScroll, { passive: true });

  /* ---- Hamburger toggle ------------------------------------------------- */
  if (hamburger && navLinks) {
    hamburger.addEventListener('click', function () {
      var isOpen = navLinks.classList.toggle('open');
      hamburger.classList.toggle('open');
      hamburger.setAttribute('aria-expanded', isOpen);
    });

    // Close menu when a link is clicked
    navLinks.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        navLinks.classList.remove('open');
        hamburger.classList.remove('open');
        hamburger.setAttribute('aria-expanded', 'false');
      });
    });
  }

  /* ---- Back to Top ------------------------------------------------------ */
  function handleBackToTop() {
    if (!backToTop) return;
    if (window.scrollY > 600) {
      backToTop.classList.add('visible');
    } else {
      backToTop.classList.remove('visible');
    }
  }
  window.addEventListener('scroll', handleBackToTop, { passive: true });

  if (backToTop) {
    backToTop.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  /* ---- Fade-up scroll animations (IntersectionObserver) ----------------- */
  if ('IntersectionObserver' in window) {
    var fadeObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          fadeObserver.unobserve(entry.target);
        }
      });
    }, {
      threshold: 0.15,
      rootMargin: '0px 0px -40px 0px'
    });

    fadeEls.forEach(function (el) {
      fadeObserver.observe(el);
    });
  } else {
    // Fallback: show everything immediately
    fadeEls.forEach(function (el) {
      el.classList.add('visible');
    });
  }

  /* ---- Active nav section highlighting ---------------------------------- */
  if ('IntersectionObserver' in window && sections.length > 0) {
    var sectionObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          var id = entry.target.getAttribute('id');
          navAnchors.forEach(function (a) {
            a.classList.remove('active');
            if (a.getAttribute('href') === '#' + id) {
              a.classList.add('active');
            }
          });
        }
      });
    }, {
      threshold: 0.3,
      rootMargin: '-80px 0px -40% 0px'
    });

    sections.forEach(function (section) {
      sectionObserver.observe(section);
    });
  }

  /* ---- Copy-to-clipboard (pip install) ---------------------------------- */
  pipCopyBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var text = btn.getAttribute('data-copy') || 'pip install recallos';

      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () {
          showCopyFeedback(btn);
        });
      } else {
        // Fallback for older browsers
        var textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        try { document.execCommand('copy'); showCopyFeedback(btn); }
        catch (e) { /* silent */ }
        document.body.removeChild(textarea);
      }
    });
  });

  function showCopyFeedback(btn) {
    var icon = btn.querySelector('.copy-icon');
    if (icon) {
      var original = icon.textContent;
      icon.textContent = '✓';
      btn.style.borderColor = 'var(--accent-turquoise)';
      setTimeout(function () {
        icon.textContent = original;
        btn.style.borderColor = '';
      }, 1500);
    }
  }

  /* ---- Lightbox for section illustrations -------------------------------- */
  var lightbox  = document.getElementById('lightbox');
  var lbImg     = lightbox ? lightbox.querySelector('.lightbox-img') : null;
  var lbCaption = lightbox ? lightbox.querySelector('.lightbox-caption') : null;
  var lbClose   = lightbox ? lightbox.querySelector('.lightbox-close') : null;
  var illustrationImgs = document.querySelectorAll('.section-illustration');

  function openLightbox(src, alt) {
    if (!lightbox || !lbImg) return;
    lbImg.src = src;
    lbImg.alt = alt;
    lbCaption.textContent = alt;
    lightbox.classList.add('active');
    document.body.style.overflow = 'hidden';
    // Move focus into the dialog
    lbClose.focus();
  }

  function closeLightbox() {
    if (!lightbox) return;
    lightbox.classList.remove('active');
    document.body.style.overflow = '';
    lbImg.src = '';
  }

  illustrationImgs.forEach(function (img) {
    img.addEventListener('click', function () {
      openLightbox(img.src, img.alt);
    });
    // Keyboard support
    img.setAttribute('tabindex', '0');
    img.setAttribute('role', 'button');
    img.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        openLightbox(img.src, img.alt);
      }
    });
  });

  if (lbClose) {
    lbClose.addEventListener('click', closeLightbox);
  }

  // Close on overlay background click
  if (lightbox) {
    lightbox.addEventListener('click', function (e) {
      if (e.target === lightbox) closeLightbox();
    });
  }

  // Close on Escape key
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && lightbox && lightbox.classList.contains('active')) {
      closeLightbox();
    }
  });

})();
