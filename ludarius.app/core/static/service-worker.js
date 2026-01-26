const CACHE_NAME = "ludarius-v3";
const ASSETS = [
  "/",
  "/offline/",
  "/static/manifest.json",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      // limpa caches antigos (se já não tiver)
      const keys = await caches.keys();
      await Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)));

      // pega controle das abas abertas sem precisar fechar
      await self.clients.claim();
    })()
  );
});


self.addEventListener("fetch", (event) => {
  const req = event.request;

  if (req.method !== "GET") return;

  const url = new URL(req.url);

  // Cache-first para estáticos
  if (url.pathname.startsWith("/static/")) {
    event.respondWith(
      caches.match(req).then((cached) => cached || fetch(req))
    );
    return;
  }

  // Network-first para páginas (inclui /tmdb/movie/... e /tmdb/tv/...)
  event.respondWith(
    fetch(req)
      .then((res) => {
        const copy = res.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(req, copy));
        return res;
      })
      .catch(() =>
        caches.match(req).then((cached) => cached || caches.match("/offline/"))
      )
  );
});

 event.respondWith(
  fetch(req)
    .then((res) => {
      const copy = res.clone();
      caches.open(CACHE_NAME).then((cache) => cache.put(req, copy));
      return res;
    })
    .catch(() => caches.match(req).then((cached) => cached || caches.match("/offline/")))
);

self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});

