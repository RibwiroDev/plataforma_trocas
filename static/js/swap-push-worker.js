self.addEventListener('push', event => {
    let payload = {};
    try { payload = event.data?.json() ?? {}; } catch {}
    const path = new URL(payload.url || '/notificacoes/', self.location.origin);
    event.waitUntil(self.registration.showNotification(payload.title || 'SWAP', {
        body: payload.body || 'Você tem uma atualização no SWAP.',
        icon: '/static/img/swap-192.png',
        data: {url: path.origin === self.location.origin ? path.href : '/notificacoes/'},
    }));
});

self.addEventListener('notificationclick', event => {
    event.notification.close();
    const target = new URL(event.notification.data.url, self.location.origin);
    if (target.origin !== self.location.origin) return;
    event.waitUntil((async () => {
        const windows = await self.clients.matchAll({type: 'window', includeUncontrolled: true});
        for (const client of windows) {
            if (new URL(client.url).origin === target.origin) {
                const updated = await client.navigate(target.href);
                if (updated) return updated.focus();
            }
        }
        return self.clients.openWindow(target.href);
    })());
});
