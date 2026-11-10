(() => {
    if (window.swapPhotoControls) return;
    window.swapPhotoControls = true;

    const gallery = document.querySelector('.existing-images');
    if (gallery) {
        gallery.id = 'fotos-enviadas';
        const heading = gallery.querySelector('h4');
        if (heading) heading.textContent = 'Fotos enviadas';
        for (const form of gallery.querySelectorAll('form[action]')) {
            if (!/^\/imagens\/\d+\/remover\/$/.test(new URL(form.action).pathname)) continue;
            form.dataset.swapRemovePhoto = '';
            const button = form.querySelector('button[type=submit]');
            if (button) {
                button.textContent = 'Excluir foto';
                button.className = 'btn btn-outline-danger btn-sm swap-remove-photo';
            }
        }
        if (location.hash === '#fotos-enviadas') gallery.scrollIntoView();
    }

    const actions = document.querySelector('.item-detail-actions');
    const edit = actions?.querySelector('a[href$="/editar/"]');
    if (edit && document.querySelector('.item-detail-main-image img')
        && !actions.querySelector('.swap-manage-photos')) {
        const manage = edit.cloneNode(true);
        manage.href = edit.href + '#fotos-enviadas';
        manage.classList.add('swap-manage-photos');
        manage.textContent = 'Gerenciar fotos';
        edit.after(manage);
    }

    function initPendingPhotos() {
        const input = document.querySelector('input[type=file][name=imagens]');
        if (!input || input.hasAttribute('data-swap-photo-preview')) return;
        input.dataset.swapPhotoPreview = '';
        input.accept = 'image/*';

        const list = document.createElement('ul');
        list.className = 'swap-pending-photos';
        list.setAttribute('aria-label', 'Fotos selecionadas');
        input.after(list);
        let previews = [];

        function render() {
            previews.forEach(url => URL.revokeObjectURL(url));
            previews = [];
            list.replaceChildren();
            for (const [index, file] of Array.from(input.files).entries()) {
                const row = document.createElement('li');
                if (file.type.startsWith('image/')) {
                    const thumbnail = document.createElement('img');
                    thumbnail.alt = '';
                    thumbnail.src = URL.createObjectURL(file);
                    previews.push(thumbnail.src);
                    row.append(thumbnail);
                }
                const name = document.createElement('span');
                name.textContent = file.name;
                const remove = document.createElement('button');
                remove.type = 'button';
                remove.className = 'btn btn-outline-danger btn-sm';
                remove.textContent = 'Remover';
                remove.setAttribute('aria-label', 'Remover foto ' + file.name);
                remove.addEventListener('click', () => {
                    const kept = new DataTransfer();
                    Array.from(input.files).forEach((selected, position) => {
                        if (position !== index) kept.items.add(selected);
                    });
                    input.files = kept.files;
                    render();
                    (list.querySelectorAll('button')[index] ?? list.lastElementChild?.querySelector('button') ?? input).focus();
                });
                row.append(name, remove);
                list.append(row);
            }
        }

        input.addEventListener('change', render);
        input.form.addEventListener('reset', () => setTimeout(render));
        new MutationObserver((records, observer) => {
            if (!input.isConnected) {
                previews.forEach(url => URL.revokeObjectURL(url));
                observer.disconnect();
            }
        }).observe(document.querySelector('.swap-content') ?? document.body, {childList: true});
        render();
    }

    initPendingPhotos();
    const content = document.querySelector('.swap-content');
    if (content) new MutationObserver(initPendingPhotos).observe(content, {childList: true});

    document.addEventListener('submit', event => {
        if (!event.target.matches('form[data-swap-remove-photo]')) return;
        if (!window.confirm('Excluir esta foto do anúncio?')) event.preventDefault();
    });
})();
