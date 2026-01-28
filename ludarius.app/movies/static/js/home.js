(function () {
  // só roda na home
  if (window.location.pathname !== "/") return;

  const section = document.getElementById("last-seen-section");
  const listEl = document.getElementById("last-seen-list");
  if (!section || !listEl) return;

  const key = "ludarius:last_seen";

  let list = [];
  try {
    list = JSON.parse(localStorage.getItem(key) || "[]");
  } catch (e) {
    list = [];
  }

  if (!list.length) return;

  // monta HTML simples
  
  listEl.innerHTML = list.map((x) => {
    const label = x.media_type === "movie" ? "Filme" : "Série/Anime";
    return `
      <li>
        <a href="${x.url}">
          ${label} • TMDB ${x.tmdb_id}
        </a>
      </li>
    `;
  }).join("");

  section.style.display = "block";
})();
