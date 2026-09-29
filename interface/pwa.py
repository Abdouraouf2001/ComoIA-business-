import streamlit.components.v1 as components 
 
 
def injecter_pwa(): 
    """ 
    Rend l'app installable (icône sur écran d'accueil / bureau). 
 
    Streamlit n'expose aucune API officielle pour modifier le <head> de la 
    page, donc on passe par un composant HTML : celui-ci s'exécute dans un 
    iframe, mais comme il est servi depuis la même origine que l'app, le 
    script peut atteindre `window.parent.document` et y ajouter le lien 
    vers le manifest, l'icône iOS et le service worker. 
 
    Idempotent (vérifie avant d'ajouter) : peut être rappelée à chaque 
    rerun sans dupliquer les balises. 
    """ 
    components.html( 
        """ 
        <script> 
        (function() { 
            const doc = window.parent.document; 
 
            if (!doc.querySelector('link[rel="manifest"]')) { 
                const manifest = doc.createElement('link'); 
                manifest.rel = 'manifest'; 
                manifest.href = '/app/static/manifest.json'; 
                doc.head.appendChild(manifest); 
            } 
 
            if (!doc.querySelector('meta[name="theme-color"]')) { 
                const themeColor = doc.createElement('meta'); 
                themeColor.name = 'theme-color'; 
                themeColor.content = '#00843D'; 
                doc.head.appendChild(themeColor); 
            } 
 
            if (!doc.querySelector('link[rel="apple-touch-icon"]')) { 
                const appleIcon = doc.createElement('link'); 
                appleIcon.rel = 'apple-touch-icon'; 
                appleIcon.href = '/app/static/apple-touch-icon.png'; 
                doc.head.appendChild(appleIcon); 
            } 
 
            const appleCapable = doc.createElement('meta'); 
            appleCapable.name = 'apple-mobile-web-app-capable'; 
            appleCapable.content = 'yes'; 
            if (!doc.querySelector('meta[name="apple-mobile-web-app-capable"]')) { 
                doc.head.appendChild(appleCapable); 
            } 
 
            if ('serviceWorker' in navigator) { 
                navigator.serviceWorker 
                    .register('/app/static/service-worker.js') 
                    .catch(function(erreur) { 
                        console.log('Échec service worker PWA :', erreur); 
                    }); 
            } 
        })(); 
        </script> 
        """, 
        height=0, 
        width=0, 
    ) 