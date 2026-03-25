
document.addEventListener('DOMContentLoaded', () => {
    console.log("Script started");
    const loader = document.getElementById('intro-loader');
    const logo = document.getElementById('logo');
    const wrapper = document.getElementById('main-wrapper');

    const createBurst = () => {
        const count = 100;
        const centerX = window.innerWidth / 2;
        const centerY = window.innerHeight / 2;
        
        // PERFORMANCE: Using DocumentFragment to batch DOM injections
        const fragment = document.createDocumentFragment();

        for (let i = 0; i < count; i++) {
            const p = document.createElement('div');
            p.className = 'particle';
            p.style.left = `${centerX}px`;
            p.style.top = `${centerY}px`;
            
            const angle = Math.random() * Math.PI * 2;
            const tx = Math.cos(angle) * (500 * Math.random());
            const ty = Math.sin(angle) * (500 * Math.random());

            const anim = p.animate([
                { transform: 'translate(0, 0) scale(1)', opacity: 1 },
                { transform: `translate(${tx}px, ${ty}px) scale(0)`, opacity: 1 }
            ], {
                duration: 1900 + Math.random() * 900,
                easing: 'cubic-bezier(0, .9, .57, 1)',
                delay: Math.random() * 80
            });
            
            if (anim) {
                anim.onfinish = () => p.remove();
            } else {
                setTimeout(() => p.remove(), 2000);
            }

            fragment.appendChild(p);
        }
        loader.appendChild(fragment);
    };

    requestAnimationFrame(() => logo.classList.add('animate-logo'));

    setTimeout(createBurst, 1150);

    setTimeout(() => {
        wrapper.classList.add('reveal');
        document.body.classList.remove('loading');
    }, 3000);

    setTimeout(() => {
        loader.style.opacity = '0';
        loader.style.transition = 'opacity 1s ease';
        setTimeout(() => loader.remove(), 1000);
    }, 3800);
});