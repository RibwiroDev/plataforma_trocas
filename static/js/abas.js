(() => {
    if (window.swapFastTabs) return;
    window.swapFastTabs = true;
    const rotas = new Set(['/', '/itens/novo/', '/propostas/recebidas/', '/propostas/enviadas/', '/perfil/']);
    const scripts = new Set(['/static/js/descricao.js', '/static/contas/localidades.js']);
    let pendente;
    let progresso;

    function limpar() {
        progresso?.remove();
        progresso = null;
        document.querySelector('.swap-dock [data-loading]')?.removeAttribute('data-loading');
        const conteudo = document.querySelector('.swap-content');
        if (conteudo) conteudo.inert = false;
    }

    document.addEventListener('click', async evento => {
        const link = evento.target.closest('.swap-dock a');
        if (!link || evento.defaultPrevented || evento.button !== 0 || evento.metaKey
            || evento.ctrlKey || evento.shiftKey || evento.altKey || link.target) return;
        const destino = new URL(link.href);
        const conteudo = document.querySelector('.swap-content');
        if (!conteudo || destino.origin !== location.origin || !rotas.has(destino.pathname)) return;
        if (typeof addSubmitLoadingState !== 'function' || typeof addAvatarPreview !== 'function') return;
        // A conversa tem polling próprio. Uma navegação normal encerra a tela anterior.
        if (document.getElementById('chat-window')) return;

        evento.preventDefault();
        pendente?.abort();
        limpar();
        if (destino.href === location.href) return;
        const controle = new AbortController();
        pendente = controle;
        conteudo.inert = true;
        link.dataset.loading = '';
        progresso = document.createElement('progress');
        progresso.className = 'swap-tab-progress';
        progresso.setAttribute('aria-label', 'Abrindo aba');
        document.body.append(progresso);

        try {
            const resposta = await fetch(destino, {signal: controle.signal, redirect: 'manual'});
            if (resposta.type === 'opaqueredirect' || !resposta.ok) throw new Error('Navegação completa');
            const html = await resposta.text();
            if (controle.signal.aborted) return;
            const pagina = new DOMParser().parseFromString(html, 'text/html');
            window.swapLegacyTheme?.(pagina, destino);
            const novoConteudo = pagina.querySelector('.swap-content');
            const novoMenu = pagina.querySelector('.swap-dock');
            if (!novoConteudo || !novoMenu) throw new Error('Layout diferente');
            if (!!pagina.querySelector('.swap-top form') !== !!document.querySelector('.swap-top form')) {
                throw new Error('Sessão alterada');
            }

            const dependencias = [...novoConteudo.querySelectorAll('script[src]')]
                .map(script => new URL(script.getAttribute('src'), destino))
                .filter(url => url.origin === destino.origin && scripts.has(url.pathname));
            novoConteudo.querySelectorAll('script').forEach(script => script.remove());
            history.pushState({swapTab: true}, '', destino);
            document.title = pagina.title;
            conteudo.replaceChildren(...novoConteudo.childNodes);
            document.querySelector('.swap-dock').replaceWith(novoMenu);
            window.scrollTo(0, 0);
            addSubmitLoadingState();
            addAvatarPreview();
            window.swapInitDescription?.();
            for (const url of dependencias) {
                const script = document.createElement('script');
                script.src = url.href;
                script.onload = script.onerror = () => script.remove();
                document.head.append(script);
            }
        } catch {
            if (!controle.signal.aborted) location.assign(destino);
        } finally {
            if (pendente === controle) {
                pendente = null;
                limpar();
            }
        }
    });

    window.addEventListener('popstate', () => {
        pendente?.abort();
        location.reload();
    });
})();
