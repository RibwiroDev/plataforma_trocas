(() => {
    const bell = document.querySelector('[data-resumo]');
    if (!bell) return;
    let pending = false;
    async function update() {
        if (document.hidden || pending) return;
        pending = true;
        try {
            const response = await fetch(bell.dataset.resumo, {cache: 'no-store'});
            if (!response.ok) return;
            const summary = await response.json();
            for (const badge of document.querySelectorAll('[data-count]')) {
                const value = summary[badge.dataset.count] || 0;
                badge.textContent = value > 99 ? '99+' : String(value);
                badge.hidden = value === 0;
            }
        } catch {
            // The next refresh will retry when the connection returns.
        } finally {
            pending = false;
        }
    }
    update();
    window.setInterval(update, 30000);
    window.addEventListener('swap:tab', update);
    document.addEventListener('visibilitychange', update);
})();
