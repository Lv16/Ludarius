  let deferredPrompt = null;
  const installBtn = document.getElementById("pwa-install-btn");

  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredPrompt = e;

    if (installBtn) installBtn.style.display = "inline-block";
  });

  if (installBtn) {
    installBtn.addEventListener("click", async () => {
      if (!deferredPrompt) return;

      deferredPrompt.prompt();
      const choice = await deferredPrompt.userChoice;

      deferredPrompt = null;
      installBtn.style.display = "none";
    });
  }

  window.addEventListener("appinstalled", () => {
    deferredPrompt = null;
    if (installBtn) installBtn.style.display = "none";
  });

  (function () {
  const meta = document.getElementById("media-meta");
  if (!meta) return;

  const mediaType = meta.dataset.mediaType;
  const tmdbId = meta.dataset.tmdbId;
  const title = meta.dataset.title || "";
  const poster = meta.dataset.poster || "";
  const url = window.location.pathname;

  if (!mediaType || !tmdbId) return;

  const key = "ludarius:last_seen";
  const maxItems = 10;

  const item = {
    media_type: mediaType,
    tmdb_id: tmdbId,
    title: title,
    poster_url: poster,
    url: url,
    seen_at: Date.now(),
  };

  let list = [];
  try {
    list = JSON.parse(localStorage.getItem(key) || "[]");
  } catch (e) {
    list = [];
  }

  list = list.filter(x => !(x.media_type === item.media_type && x.tmdb_id === item.tmdb_id));

  list.unshift(item);

  list = list.slice(0, maxItems);

  localStorage.setItem(key, JSON.stringify(list));
})();

(function () {
  if (window.location.pathname !== "/") return;

  const section = document.getElementById("last-seen-section");
  const listEl = document.getElementById("last-seen-list");
  const clearBtn = document.getElementById("last-seen-clear");
  if (!section || !listEl) return;

  const key = "ludarius:last_seen";

  let list = [];
  try {
    list = JSON.parse(localStorage.getItem(key) || "[]");
  } catch (e) {
    list = [];
  }

  if (!list.length) return;

const render = () => {
  if (!list.length) {
    section.style.display = "none";
    return;
  }

  listEl.innerHTML = list.map((x) => {
    const label = x.media_type === "movie" ? "Filme" : "Série/Anime";
    const safeTitle = (x.title || `${label} • TMDB ${x.tmdb_id}`);
    const posterHtml = x.poster_url
      ? `<img src="${x.poster_url}" alt="Poster" width="36" style="vertical-align: middle;"> `
      : "";

    return `
      <li>
        ${posterHtml}
        <a href="${x.url}">
          <strong>${safeTitle}</strong>
        </a>
        <span> — ${label}</span>

        <button
          type="button"
          class="last-seen-remove"
          data-media-type="${x.media_type}"
          data-tmdb-id="${x.tmdb_id}"
          style="margin-left: 8px;"
          aria-label="Remover do histórico"
          title="Remover"
        >
          ×
        </button>
      </li>
    `;
  }).join("");

  section.style.display = "block";
};


  render();

  listEl.addEventListener("click", (e) => {
  const btn = e.target.closest(".last-seen-remove");
  if (!btn) return;

  const mt = btn.dataset.mediaType;
  const id = btn.dataset.tmdbId;

  list = list.filter(x => !(x.media_type === mt && String(x.tmdb_id) === String(id)));
  localStorage.setItem(key, JSON.stringify(list));
  if (!confirm("Remover do histórico?")) return;
  render();
});




  if (clearBtn) {
    clearBtn.addEventListener("click", (e) => {
      e.preventDefault();
      localStorage.removeItem(key);
      list = [];
      render();
    });
  }
})();

(async function () {
  if (!("serviceWorker" in navigator)) return;

  const updateBox = document.getElementById("sw-update");
  const updateBtn = document.getElementById("sw-update-btn");

  const showUpdate = (reg) => {
    if (!updateBox || !updateBtn) return;

    updateBox.style.display = "block";

    updateBtn.onclick = () => {
      if (reg.waiting) {
        reg.waiting.postMessage({ type: "SKIP_WAITING" });
      }
    };
  };

  let reg;
  try {
    reg = await navigator.serviceWorker.register("/static/service-worker.js");
  } catch (err) {
    console.warn("Falha ao registrar o service worker.", err);
    return;
  }

  reg.addEventListener("updatefound", () => {
    const newWorker = reg.installing;
    if (!newWorker) return;

    newWorker.addEventListener("statechange", () => {

      if (newWorker.state === "installed" && navigator.serviceWorker.controller) {
        showUpdate(reg);
      }
    });
  });

  navigator.serviceWorker.addEventListener("controllerchange", () => {
    window.location.reload();
  });
})();



