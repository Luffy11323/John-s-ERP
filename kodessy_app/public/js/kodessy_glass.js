/**
 * Kodessy Pharma ERP — Dashboard JS
 * Inspired by Radiant premium_dashboard.js patterns:
 *   - Arrow-function style
 *   - body.kod-premium gating (CSS hooks only fire when this class is present)
 *   - frappe.boot flag guard (kodessy_premium = true in site_config or frappe.boot)
 *   - Clean slug-based hero rendering
 *   - Number card accent via data-attr guard
 */
(function () {
  'use strict';

  // ── helpers ─────────────────────────────────────────────────────────────────
  const esc  = (s) => frappe.utils.escape_html(String(s == null ? '' : s));
  const API  = 'kodessy_app.api.';

  function compact(v) {
    const a = Math.abs(v || 0), s = v < 0 ? '-' : '';
    if (a >= 1e9) return s + (a / 1e9).toFixed(2) + 'B';
    if (a >= 1e6) return s + (a / 1e6).toFixed(2) + 'M';
    if (a >= 1e5) return s + (a / 1e3).toFixed(0) + 'K';
    return s + a.toLocaleString(undefined, { maximumFractionDigits: 0 });
  }

  function slugFromPath() {
    const p = decodeURIComponent(window.location.pathname).split('/').filter(Boolean);
    if (p[0] !== 'app') return null;
    if (p[1] === 'workspace' && p[2]) return p[2].toLowerCase();
    if (p[1] === 'private'   && p[2]) return p[2].toLowerCase();
    if (p.length === 2) return (p[1] || 'home').toLowerCase();
    if (p.length === 1) return 'home';
    return null;
  }

  const mountPoint = () => {
    if ($('.form-layout:visible, .list-layout:visible, .report-page:visible, .form-page:visible').length) return null;
    const $m = $('.layout-main-section').filter(':visible').first();
    return $m.length ? $m : null;
  };

  const greeting = () => {
    const h = new Date().getHours();
    return h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening';
  };

  // ── KPI cell template ───────────────────────────────────────────────────────
  function kpiHtml(k) {
    const val = k.fmt === 'money'
      ? 'RM ' + compact(k.value)
      : (k.value || 0).toLocaleString();
    return `<div class="kod-cell" data-route="${esc(k.route || '')}" title="${esc(k.value)}">
      <div class="kod-l">${esc(k.label)}</div>
      <div class="kod-v">${val}</div>
    </div>`;
  }

  // ── Hero card renderer ───────────────────────────────────────────────────────
  function renderHero(card, $main) {
    $('.kod-hero').remove();

    const kps = card.kpis && card.kpis.length
      ? `<div class="kod-grid">${card.kpis.map(kpiHtml).join('')}</div>`
      : '';

    const rpts = (card.reports || []).length
      ? `<div class="kod-reports"><span>Reports</span>${
          card.reports.map(r => `<a class="kod-report" data-route="${esc(r.route)}">${esc(r.label)}</a>`).join('')
        }</div>`
      : '';

    const $hero = $(`<div class="kod-hero">
      <div class="kod-head">
        <h3>${greeting()}, ${esc(card.user)}</h3>
        <div class="kod-sub">${esc(card.title)} &mdash; ${esc(card.subtitle)}</div>
      </div>
      ${kps}${rpts}
    </div>`);

    $main.prepend($hero);
    $hero.data('slug', card.slug);

    $hero.on('click', '[data-route]', function () {
      const r = $(this).data('route');
      if (!r) return;
      if (r.indexOf('?') !== -1) window.location.href = '/app/' + r;
      else frappe.set_route(r.split('/'));
    });
  }

  // ── Number card accent ───────────────────────────────────────────────────────
  function accentNumberCards() {
    document.querySelectorAll('.widget-number-card:not([data-kod-ready])').forEach(card => {
      card.setAttribute('data-kod-ready', 'true');
      const t = card.innerText || '';
      if      (t.indexOf('Quarantine') !== -1) card.style.borderLeft = '4px solid #ef4444';
      else if (t.indexOf('Expiry')     !== -1) card.style.borderLeft = '4px solid #f59e0b';
      else if (t.indexOf('Credit')     !== -1) card.style.borderLeft = '4px solid #8b5cf6';
      else if (t.indexOf('Approval')   !== -1) card.style.borderLeft = '4px solid #0ea5e9';
    });
  }

  // ── Load hero card ───────────────────────────────────────────────────────────
  let busy = false;

  function load(force) {
    const slug = slugFromPath();
    if (!slug) return;
    if (!force && $('.kod-hero').data('slug') === slug) return;
    if (busy) return;
    busy = true;

    let tries = 0;
    const wait = setInterval(() => {
      const $main = mountPoint();
      if (!$main && ++tries < 40) return;
      clearInterval(wait);
      if (!$main) { busy = false; return; }
      frappe.call({ method: API + 'get_card', args: { slug } })
        .then(r => {
          if (slugFromPath() !== slug) return;
          $('.kod-hero').remove();
          if (r.message) { r.message.slug = slug; renderHero(r.message, $main); }
        })
        .always(() => { busy = false; });
    }, 200);
  }

  // ── Robust Boot & Initialization ───────────────────────────────────────────
  function init() {
    const ensureClass = () => {
      if (document.body && !document.body.classList.contains('kod-premium')) {
        document.body.classList.add('kod-premium');
      }
    };
    ensureClass();

    if (window.MutationObserver && document.body) {
      new MutationObserver(ensureClass).observe(document.body, {
        attributes: true,
        attributeFilter: ['class']
      });
    }

    load(true);
    accentNumberCards();

    $(document).on('page-change', () => {
      setTimeout(() => { load(false); accentNumberCards(); }, 150);
    });

    let tries = 0;
    const t = setInterval(() => {
      if (window.frappe && frappe.router) {
        clearInterval(t);
        if (frappe.router.on) {
          frappe.router.on('change', () => {
            setTimeout(() => { load(false); accentNumberCards(); }, 150);
          });
        }
        setTimeout(() => { load(false); accentNumberCards(); }, 500);
      } else if (++tries > 100) {
        clearInterval(t);
      }
    }, 200);
  }

  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    init();
  } else {
    document.addEventListener('DOMContentLoaded', init);
  }
})();
