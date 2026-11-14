(() => {
    const control = document.querySelector('[data-push-config]');
    if (!control) return;
    const button = control.querySelector('button');
    const status = control.querySelector('[role=status]');
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        status.textContent = /iPhone|iPad|iPod/.test(navigator.userAgent)
            ? 'No iPhone, abra o SWAP pelo atalho da Tela de Início para ativar.'
            : 'Este navegador não oferece notificações do sistema.';
        return;
    }

    let registration;
    let key;
    let active = false;

    function showState() {
        button.textContent = active ? 'Desativar notificações' : 'Ativar notificações';
        button.disabled = false;
    }

    async function save(subscription, deactivate = false) {
        const response = await fetch(control.dataset.pushSave, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': control.querySelector('[name=csrfmiddlewaretoken]').value,
            },
            body: JSON.stringify({...subscription.toJSON(), desativar: deactivate}),
        });
        if (!response.ok) throw new Error('Não foi possível atualizar as notificações.');
    }

    async function setup() {
        try {
            const response = await fetch(control.dataset.pushConfig);
            const config = await response.json();
            if (!response.ok || !config.chave) {
                status.textContent = 'As notificações do sistema ainda não estão disponíveis.';
                return;
            }
            const base64 = config.chave.replace(/-/g, '+').replace(/_/g, '/');
            key = Uint8Array.from(atob(base64.padEnd(Math.ceil(base64.length / 4) * 4, '=')), char => char.charCodeAt(0));
            await navigator.serviceWorker.register('/swap-push-worker.js');
            registration = await navigator.serviceWorker.ready;
            const subscription = await registration.pushManager.getSubscription();
            active = !!subscription && localStorage.getItem('swap-push-session') === control.dataset.pushAccount;
            showState();
        } catch {
            status.textContent = 'Não foi possível preparar as notificações. Atualize a página e tente novamente.';
        }
    }

    button.addEventListener('click', async () => {
        button.disabled = true;
        status.textContent = '';
        try {
            if (active) {
                const subscription = await registration.pushManager.getSubscription();
                if (subscription) {
                    await save(subscription, true);
                    await subscription.unsubscribe();
                }
                localStorage.removeItem('swap-push-session');
                active = false;
            } else {
                const subscription = await registration.pushManager.subscribe({userVisibleOnly: true, applicationServerKey: key});
                await save(subscription);
                localStorage.setItem('swap-push-session', control.dataset.pushAccount);
                active = true;
            }
            status.textContent = active ? 'Notificações ativadas neste dispositivo.' : 'Notificações desativadas neste dispositivo.';
        } catch {
            status.textContent = 'Não foi possível alterar as notificações. Confira a permissão do navegador.';
        } finally {
            showState();
        }
    });
    setup();
})();
