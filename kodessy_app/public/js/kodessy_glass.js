/**
 * Kodessy glass dashboard: one large hover-glow card per workspace with KPI cells
 * separated by thin dividers, plus report shortcuts. Also accents native Number Cards.
 */
(function () {
  'use strict';

  var API = 'kodessy_app.api.';

  function esc(s) {
    return frappe.utils.escape_html(String(s == null ? '' : s));
  }

  function compact(v) {
    var a = Math.abs(v || 0), s = v < 0 ? '-' : '';
    if (a >= 1e9) return s + (a / 1e9).toFixed(2) + 'B';
    if (a >= 1e6) return s + (a / 1e6).toFixed(2) + 'M';
    if (a >= 1e5) return s + (a / 1e3).toFixed(0) + 'K';
    return s + a.toLocaleString(undefined, { maximumFractionDigits: 0 });
  }

  function slugFromPath() {
    var p = decodeURIComponent(window.location.pathname).split('/').filter(Boolean);
    if (p[0] !== 'app') return null;
    if (p[1] === 'workspace' && p[2]) return p[2].toLowerCase();
    if (p[1] === 'private' && p[2]) return p[2].toLowerCase();
    if (p.length === 2) return (p[1] || 'home').toLowerCase();
    if (p.length === 1) return 'home';
    return null;
  }

  function mountPoint() {
    if ($('.form-layout:visible, .list-layout:visible, .report-page:visible, .form-page:visible').length) return null;
    var $m = $('.layout-main-section').filter(':visible').first();
    return $m.length ? $m : null;
  }

  function greeting() {
    var h = new Date().getHours();
    return h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening';
  }

  function render(card, $main) {
    $('.kod-hero').remove();
    var cells = card.kpis.map(function (k) {
      var val = k.fmt === 'money' ? 'RM ' + compact(k.value) : (k.value || 0).toLocaleString();
      return '<div class="kod-cell" data-route="' + esc(k.route) + '" title="' + esc(k.value) + '">' +
        '<div class="kod-l">' + esc(k.label) + '</div><div class="kod-v">' + val + '</div></div>';
    }).join('');
    var reports = (card.reports || []).map(function (r) {
      return '<a class="kod-report" data-route="' + esc(r.route) + '">' + esc(r.label) + '</a>';
    }).join('');
    var html = '<div class="kod-hero kodessy-glass-card">' +
      '<div class="kod-head"><h3>' + greeting() + ', ' + esc(card.user) + '</h3>' +
      '<div class="kod-sub">' + esc(card.title) + ' &mdash; ' + esc(card.subtitle) + '</div></div>' +
      '<div class="kod-grid">' + cells + '</div>' +
      (reports ? '<div class="kod-reports"><span>Reports</span>' + reports + '</div>' : '') +
      '</div>';
    var $hero = $(html);
    $main.prepend($hero);
    $hero.data('slug', card.slug);
    $hero.on('click', '[data-route]', function () {
      var r = $(this).data('route');
      if (!r) return;
      if (r.indexOf('?') !== -1) window.location.href = '/app/' + r;
      else frappe.set_route(r.split('/'));
    });
  }

  var busy = false;
  function load(force) {
    var slug = slugFromPath();
    if (!slug || busy) return;
    if (!force && $('.kod-hero').data('slug') === slug) return;
    busy = true;
    var tries = 0;
    var wait = setInterval(function () {
      var $main = mountPoint();
      if (!$main && ++tries < 40) return;
      clearInterval(wait);
      if (!$main) { busy = false; return; }
      frappe.call({ method: API + 'get_card', args: { slug: slug } }).then(function (r) {
        if (slugFromPath() !== slug) return;
        $('.kod-hero').remove();
        if (r.message) { r.message.slug = slug; render(r.message, $main); }
      }).always(function () { busy = false; });
    }, 200);
  }

  function accentNumberCards() {
    document.querySelectorAll('.widget-number-card:not([data-glass-ready])').forEach(function (card) {
      card.setAttribute('data-glass-ready', 'true');
      var t = card.innerText || '';
      if (t.indexOf('Quarantine') !== -1) card.style.borderLeft = '4px solid #ef4444';
      else if (t.indexOf('Expiry') !== -1) card.style.borderLeft = '4px solid #f59e0b';
      else if (t.indexOf('Credit') !== -1) card.style.borderLeft = '4px solid #8b5cf6';
      else if (t.indexOf('Approval') !== -1) card.style.borderLeft = '4px solid #0ea5e9';
    });
  }

  // frappe.router may not exist when this script is parsed, so wait for the desk to be ready.
  $(document).ready(function () {
    var tries = 0;
    var t = setInterval(function () {
      if (window.frappe && frappe.router && frappe.router.on) {
        clearInterval(t);
        frappe.router.on('change', function () {
          setTimeout(function () { load(false); accentNumberCards(); }, 150);
        });
        setTimeout(function () { load(false); accentNumberCards(); }, 600);
      } else if (++tries > 100) {
        clearInterval(t);
      }
    }, 200);
  });
})();
