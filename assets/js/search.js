(function () {
  var script = document.currentScript;
  var input = document.getElementById("search-input");
  var status = document.getElementById("search-status");
  var results = document.getElementById("search-results");
  var posts = null;

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function snippet(content, term) {
    var i = content.toLowerCase().indexOf(term);
    if (i < 0) return content.slice(0, 200) + "…";
    var start = Math.max(0, i - 80);
    return (start > 0 ? "…" : "") + content.slice(start, i + 160) + "…";
  }

  function render() {
    var terms = input.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
    results.innerHTML = "";
    if (!terms.length) { status.textContent = ""; return; }

    var scored = [];
    posts.forEach(function (p) {
      var title = p.title.toLowerCase();
      var meta = p.categories.toLowerCase();
      var body = p.content.toLowerCase();
      var score = 0;
      for (var t = 0; t < terms.length; t++) {
        var term = terms[t];
        var s = (title.indexOf(term) >= 0 ? 10 : 0) + (meta.indexOf(term) >= 0 ? 5 : 0) + (body.indexOf(term) >= 0 ? 1 : 0);
        if (!s) return; // every term must match somewhere
        score += s;
      }
      scored.push({ post: p, score: score });
    });
    scored.sort(function (a, b) { return b.score - a.score; });

    status.textContent = scored.length + (scored.length === 1 ? " result" : " results");
    results.innerHTML = scored.slice(0, 50).map(function (r) {
      var p = r.post;
      return '<li><span class="post-meta">' + escapeHtml(p.date) + '</span>' +
        '<h3><a class="post-link" href="' + escapeHtml(p.url) + '">' + escapeHtml(p.title) + '</a></h3>' +
        '<p>' + escapeHtml(snippet(p.content, terms[0])) + '</p></li>';
    }).join("");
  }

  status.textContent = "Loading index…";
  fetch(script.dataset.index)
    .then(function (r) { return r.json(); })
    .then(function (data) {
      posts = data;
      status.textContent = "";
      var q = new URLSearchParams(location.search).get("q");
      if (q) input.value = q;
      input.addEventListener("input", render);
      render();
    })
    .catch(function () { status.textContent = "Could not load the search index."; });
})();
