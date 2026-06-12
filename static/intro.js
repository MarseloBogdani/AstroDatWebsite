// 1. Ορισμός της συνάρτησης έκρηξης εκτός για να είναι διαθέσιμη αμέσως
// 1. Ορισμός της συνάρτησης έκρηξης εκτός για μέγιστη ταχύτητα
function createExplosion() {
    const container = document.getElementById('intro-loader');
    if (!container) return;

    const particleCount = 70; // Αυξημένη πυκνότητα
    for (let i = 0; i < particleCount; i++) {
        const p = document.createElement('div');
        p.className = 'particle';
        
        const size = Math.random() * 2 + 1;
        p.style.width = `${size}px`;
        p.style.height = `${size}px`;
        p.style.position = 'absolute';

        const angle = Math.random() * Math.PI * 2;
        const velocity = Math.random() * 600 + 200; // Πιο δυνατή έκρηξη
        const destX = Math.cos(angle) * velocity;
        const destY = Math.sin(angle) * velocity;
        const destZ = (Math.random() - 0.2) * 1800; // Μεγαλύτερο εύρος Z

        container.appendChild(p);

        p.animate([
            { transform: 'translate(-50%, -50%) translateZ(0) scale(1)', opacity: 1 },
            { 
                transform: `translate(calc(-50% + ${destX}px), calc(-50% + ${destY}px)) translateZ(${destZ}px) scale(${destZ > 0 ? 5 : 0.1})`, 
                opacity: 0,
                filter: destZ > 600 ? 'blur(5px)' : 'blur(0px)' 
            }
        ], {
            duration: 1200 + Math.random() * 800,
            easing: 'cubic-bezier(0.1, 0.8, 0.4, 1)',
            fill: 'forwards'
        }).onfinish = () => p.remove();
    }
}

// 2. Άμεση εκτέλεση (IIFE) για εξάλειψη του lag στο Refresh
(function initAstroLoader() {
    // Ψάχνουμε το logo αμέσως, χωρίς αναμονή DOMContentLoaded
    const startAnimation = () => {
        const logo = document.getElementById('logo');
        const loader = document.getElementById('intro-loader');
        const wrapper = document.getElementById('main-wrapper');
        const body = document.body;

        // Αν δεν βρέθηκε ακόμα, ξαναπροσπαθούμε στο επόμενο frame (περίπου 16ms)
        if (!logo) return requestAnimationFrame(startAnimation);

        // --- ΕΝΑΡΞΗ ΑΚΑΡΙΑΙΑ ---
        logo.classList.add('animate-logo');

        // --- ΧΡΟΝΙΣΜΟΣ IMPACT (1200ms) ---
        setTimeout(() => {
            // ΛΕΠΤΟΜΕΡΕΙΑ 1: Πρώτα βγαίνουν τα particles
            createExplosion();
            // ΙΔΕΑ: Hyperspace Star-Stretch
            body.classList.add('warp-speed'); 
        }, 1200);

        // --- ΧΡΟΝΙΣΜΟΣ RECOVERY (1900ms) ---
        setTimeout(() => {
            // Επαναφορά αστεριών
            body.classList.remove('warp-speed');
        }, 1900);

        // --- ΧΡΟΝΙΣΜΟΣ REVEAL (3400ms) ---
        setTimeout(() => {
            if (loader) {
                loader.style.opacity = '0';
                loader.style.transition = 'opacity 0.8s ease';
                
                setTimeout(() => {
                    loader.remove();
                    body.classList.remove('loading');
                    // ΙΔΕΑ: Camera Shake κατά το reveal
                    if (wrapper) wrapper.classList.add('animate-reveal');
                }, 800);
            }
        }, 3400);
    };

    startAnimation();
})();