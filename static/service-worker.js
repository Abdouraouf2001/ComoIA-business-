// Service worker minimal : condition technique requise par les navigateurs 
// pour proposer "Installer l'application". Ne fait pas de cache hors-ligne 
// pour l'instant (l'app a besoin du serveur Streamlit de toute façon). 
self.addEventListener("install", (event) => { 
self.skipWaiting(); 
}); 
self.addEventListener("activate", (event) => { 
event.waitUntil(self.clients.claim()); 
}); 
self.addEventListener("fetch", (event) => { 
event.respondWith(fetch(event.request)); 
}); 