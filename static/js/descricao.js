window.swapInitDescription = () => {
    const form = document.querySelector('form[data-sugestao-url]')
        ?? (location.pathname === '/itens/novo/' ? document.querySelector('#id_titulo')?.form : null);
    const titulo = form?.elements.titulo;
    const descricao = form?.elements.descricao;
    if (!titulo || !descricao || form.querySelector('.swap-description')) return;

    const panel = document.createElement('div');
    panel.className = 'swap-description';
    panel.hidden = true;
    const preview = document.createElement('p');
    const status = document.createElement('small');
    status.setAttribute('role', 'status');
    const use = document.createElement('button');
    use.type = 'button';
    use.className = 'swap-account';
    use.textContent = 'Usar sugestão';
    panel.append(preview, use);

    let version = 0;
    const update = () => {
        version++;
        const nome = titulo.value.trim();
        panel.hidden = nome.length < 3;
        preview.textContent = nome.length >= 3
            ? `${nome} disponível para troca. Envie uma proposta e vamos conversar!` : '';
        status.textContent = '';
    };
    use.addEventListener('click', () => {
        if (!preview.textContent) return;
        descricao.value = descricao.value.trim()
            ? `${descricao.value.trim()}\n\n${preview.textContent}`
            : preview.textContent;
        descricao.focus();
    });

    const endpoint = form.dataset.sugestaoUrl;
    if (endpoint) {
        const ai = document.createElement('button');
        ai.type = 'button';
        ai.className = 'swap-account';
        ai.textContent = 'Gerar com IA';
        ai.addEventListener('click', async () => {
            const requested = version;
            ai.disabled = true;
            status.textContent = 'Gerando sugestão…';
            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    body: new URLSearchParams({titulo: titulo.value.trim()}),
                    headers: {'X-CSRFToken': form.elements.csrfmiddlewaretoken.value},
                    signal: AbortSignal.timeout(10000),
                });
                const result = await response.json();
                if (requested !== version) return;
                if (!response.ok) {
                    status.textContent = result.erro;
                    return;
                }
                preview.textContent = result.descricao;
                status.textContent = 'Sugestão de IA pronta para revisar.';
            } catch {
                if (requested === version) status.textContent = 'IA indisponível. Você pode usar o rascunho.';
            } finally {
                ai.disabled = false;
            }
        });
        panel.append(ai);
    }
    panel.append(status);
    descricao.after(panel);
    titulo.addEventListener('input', update);
    update();
};
window.swapInitDescription();
