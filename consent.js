(function () {
  var KEY = 'wf_consent', d = document;
  function get() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function set(v) { try { localStorage.setItem(KEY, v); } catch (e) {} }
  function css() {
    var s = d.createElement('style');
    s.textContent =
      '#wfc{position:fixed;z-index:60;inset-inline:0;bottom:0;padding:12px max(16px,env(safe-area-inset-right,0px)) max(12px,env(safe-area-inset-bottom,0px)) max(16px,env(safe-area-inset-left,0px));display:flex;justify-content:center;pointer-events:none}' +
      '#wfc .b{pointer-events:auto;width:100%;max-width:560px;box-sizing:border-box;background:#fff;color:#3d3929;border:1px solid #D3D0C7;border-radius:18px;padding:16px;box-shadow:0 10px 30px rgba(61,57,41,.22);font:16px/1.7 Tajawal,system-ui,sans-serif;direction:rtl;text-align:right}' +
      '#wfc p{margin:0 0 12px}#wfc a{color:#8f3f1f;font-weight:700}' +
      '#wfc .r{display:flex;flex-wrap:wrap;gap:10px}' +
      '#wfc button{flex:1 1 120px;min-height:48px;border-radius:999px;font:inherit;font-weight:800;cursor:pointer;border:2px solid #3d3929;background:transparent;color:#3d3929}' +
      '#wfc button.y{background:#A44E30;border-color:#A44E30;color:#fff}' +
      '#wfc button:focus-visible{outline:3px solid #D6A62D;outline-offset:2px}';
    d.head.appendChild(s);
  }
  function show() {
    if (d.getElementById('wfc')) return;
    css();
    var w = d.createElement('div');
    w.id = 'wfc';
    w.innerHTML =
      '<div class="b" role="region" aria-label="الموافقة على ملفات تعريف الارتباط">' +
      '<p>نستخدم Google Analytics لقياس الزيارات وتحسين الموقع، وهو يضع ملفات تعريف ارتباط (Cookies) في متصفحك. لن نفعّله إلا بموافقتك. <a href="/privacy.html">التفاصيل</a></p>' +
      '<div class="r"><button type="button" class="y" id="wfcY">موافق</button><button type="button" id="wfcN">رفض</button></div></div>';
    d.body.appendChild(w);
    d.getElementById('wfcY').onclick = function () { set('1'); w.remove(); if (window.wfConsentLoad) window.wfConsentLoad(); };
    d.getElementById('wfcN').onclick = function () { set('0'); w.remove(); };
  }
  function init() {
    if (get() === null) show();
    var r = d.getElementById('wfc-reset');
    if (r) r.addEventListener('click', function (e) {
      e.preventDefault();
      try { localStorage.removeItem(KEY); } catch (x) {}
      show();
    });
  }
  if (d.readyState === 'loading') d.addEventListener('DOMContentLoaded', init); else init();
})();
/* store badge colors: mark .tag/.merchant with the store key so CSS can color them */
(function () {
  var d = document, K = { amazon: 1, noon: 1, aliexpress: 1 };
  function run() {
    d.querySelectorAll('.ocard .tag,.deal .merchant').forEach(function (e) {
      var s = (e.textContent || '').trim().toLowerCase();
      if (K[s]) e.setAttribute('data-s', s);
    });
  }
  if (d.readyState === 'loading') d.addEventListener('DOMContentLoaded', run); else run();
})();
