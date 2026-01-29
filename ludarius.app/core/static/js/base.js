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
  const target = e.target instanceof Element ? e.target : e.target.parentElement;
  const btn = target ? target.closest(".last-seen-remove") : null;
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

(function () {
  document.addEventListener("click", async (e) => {
    const target = e.target instanceof Element ? e.target : e.target.parentElement;
    const btn = target ? target.closest(".share-btn") : null;
    if (!btn) return;

    const title = btn.dataset.title || "Ludarius";
    const url = btn.dataset.url || window.location.href;
    const poster = btn.dataset.poster || "";
    const rating = btn.dataset.rating || "";
    const comment = btn.dataset.comment || "";
    const shareMenu = document.getElementById("share-menu");
    if (!shareMenu) return;

    shareMenu.dataset.title = title;
    shareMenu.dataset.url = url;
    shareMenu.dataset.poster = poster;
    shareMenu.dataset.rating = rating;
    shareMenu.dataset.comment = comment;
    shareMenu.style.display = "block";
  });
})();

(function () {
  const shareMenu = document.getElementById("share-menu");
  if (!shareMenu) return;

  const closeMenu = () => {
    shareMenu.style.display = "none";
  };

  const loadImage = (src) => new Promise((resolve, reject) => {
    if (!src) return reject(new Error("no_src"));
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error("load_fail"));
    img.src = src;
  });

  const wrapText = (ctx, text, x, y, maxWidth, lineHeight, maxLines) => {
    const words = (text || "").split(" ");
    let line = "";
    let lines = 0;
    for (let i = 0; i < words.length; i += 1) {
      const testLine = line + words[i] + " ";
      const metrics = ctx.measureText(testLine);
      if (metrics.width > maxWidth && i > 0) {
        ctx.fillText(line.trim(), x, y);
        line = words[i] + " ";
        y += lineHeight;
        lines += 1;
        if (lines >= maxLines - 1) break;
      } else {
        line = testLine;
      }
    }
    ctx.fillText(line.trim(), x, y);
  };

  const createShareImage = async (data) => {
    const width = 1080;
    const height = 1920;
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("no_canvas");

    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, "#0b0b10");
    gradient.addColorStop(1, "#1b1b2a");
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);

    let img;
    try {
      img = await loadImage(data.poster);
    } catch (e) {
      img = null;
    }

    if (img) {
      const imgW = width * 0.8;
      const imgH = imgW * 1.5;
      const imgX = (width - imgW) / 2;
      const imgY = 220;
      ctx.save();
      ctx.shadowColor = "rgba(0,0,0,0.35)";
      ctx.shadowBlur = 24;
      ctx.drawImage(img, imgX, imgY, imgW, imgH);
      ctx.restore();
    }

    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 64px Arial";
    wrapText(ctx, data.title, 120, 120, width - 240, 72, 2);

    const drawStar = (ctx, x, y, radius, filled) => {
      const inner = radius * 0.5;
      ctx.beginPath();
      for (let i = 0; i < 10; i += 1) {
        const angle = (Math.PI / 5) * i - Math.PI / 2;
        const r = i % 2 === 0 ? radius : inner;
        const px = x + Math.cos(angle) * r;
        const py = y + Math.sin(angle) * r;
        if (i === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.closePath();
      if (filled) {
        ctx.fillStyle = "#ffd166";
        ctx.fill();
      } else {
        ctx.strokeStyle = "#ffd166";
        ctx.lineWidth = 3;
        ctx.stroke();
      }
    };

    if (data.rating) {
      const score = Number(data.rating);
      if (!Number.isNaN(score)) {
        const stars = Math.max(0, Math.min(5, Math.round(score / 2)));
        const startX = 120;
        const startY = height - 320;
        const size = 22;
        for (let i = 0; i < 5; i += 1) {
          drawStar(ctx, startX + i * 52, startY, size, i < stars);
        }
        ctx.font = "bold 40px Arial";
        ctx.fillStyle = "#ffffff";
        ctx.fillText(`Minha nota: ${score}/10`, 120, height - 250);
      }
    }

    if (data.comment) {
      ctx.font = "28px Arial";
      ctx.fillStyle = "#d7d7e0";
      wrapText(ctx, `"${data.comment}"`, 120, height - 190, width - 240, 40, 3);
    }

    ctx.font = "28px Arial";
    ctx.fillStyle = "#d7d7e0";
    ctx.fillText("Ludarius", 120, height - 80);

    const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/png", 0.92));
    if (!blob) throw new Error("no_blob");
    return new File([blob], "ludarius-share.png", { type: "image/png" });
  };

  const copyToClipboard = async (url) => {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(url);
      alert("Link copiado!");
      return true;
    }

    const textarea = document.createElement("textarea");
    textarea.value = url;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.top = "-9999px";
    document.body.appendChild(textarea);
    textarea.select();
    const copied = document.execCommand("copy");
    document.body.removeChild(textarea);
    if (copied) {
      alert("Link copiado!");
      return true;
    }
    return false;
  };

  shareMenu.addEventListener("click", async (e) => {
    const target = e.target instanceof Element ? e.target : e.target.parentElement;
    const actionBtn = target ? target.closest("[data-share-action]") : null;
    if (!actionBtn) return;

    const action = actionBtn.getAttribute("data-share-action");
    const title = shareMenu.dataset.title || "Ludarius";
    const url = shareMenu.dataset.url || window.location.href;
    const poster = shareMenu.dataset.poster || "";
    const rating = shareMenu.dataset.rating || "";
    const comment = shareMenu.dataset.comment || "";
    const encodedUrl = encodeURIComponent(url);
    const encodedTitle = encodeURIComponent(title);

    try {
      if (action === "close") {
        closeMenu();
        return;
      }

      if (action === "instagram") {
        try {
          const file = await createShareImage({ title, poster, rating, comment });
          const objectUrl = URL.createObjectURL(file);
          const link = document.createElement("a");
          link.href = objectUrl;
          link.download = "ludarius-share.png";
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
          alert("Imagem salva. Abra o Instagram e compartilhe nos Stories.");
          closeMenu();
          return;
        } catch (err) {
          const ok = await copyToClipboard(url);
          if (!ok) alert("Não foi possível compartilhar no Instagram. Copie o link da barra de endereços.");
          closeMenu();
          return;
        }
      }

      if (action === "copy") {
        const ok = await copyToClipboard(url);
        if (!ok) alert("Não foi possível copiar. Copie o link da barra de endereços.");
        closeMenu();
        return;
      }

      if (action === "whatsapp") {
        window.open(`https://wa.me/?text=${encodedTitle}%20${encodedUrl}`, "_blank", "noopener");
        closeMenu();
        return;
      }

      if (action === "telegram") {
        window.open(`https://t.me/share/url?url=${encodedUrl}&text=${encodedTitle}`, "_blank", "noopener");
        closeMenu();
        return;
      }

      if (action === "twitter") {
        window.open(`https://twitter.com/intent/tweet?text=${encodedTitle}&url=${encodedUrl}`, "_blank", "noopener");
        closeMenu();
        return;
      }

      if (action === "facebook") {
        window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`, "_blank", "noopener");
        closeMenu();
        return;
      }
    } catch (err) {
      alert("Não foi possível compartilhar. Copie o link da barra de endereços.");
      closeMenu();
    }
  });

  shareMenu.addEventListener("click", (e) => {
    if (e.target === shareMenu) closeMenu();
  });
})();




