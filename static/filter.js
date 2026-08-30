// Progressive enhancement only: the full list is already in the HTML.
(function () {
  var box = document.getElementById('filter');
  var input = document.getElementById('q');
  var count = document.getElementById('filter-count');
  if (!box || !input) return;
  box.hidden = false;

  var items = [].slice.call(document.querySelectorAll('ul.bills > li'));
  var timer;

  function apply() {
    var q = input.value.trim().toLowerCase();
    var shown = 0;
    items.forEach(function (li) {
      var hit = !q || li.dataset.search.toLowerCase().indexOf(q) !== -1;
      li.hidden = !hit;
      if (hit) shown++;
    });
    document.querySelectorAll('section').forEach(function (s) {
      s.hidden = !s.querySelector('ul.bills > li:not([hidden])');
    });
    count.textContent = q ? shown + ' of ' + items.length + ' listings match.' : '';
  }

  input.addEventListener('input', function () {
    clearTimeout(timer);
    timer = setTimeout(apply, 300); // let a screen reader finish the keystroke
  });
})();
