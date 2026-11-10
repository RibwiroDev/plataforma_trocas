'use strict';

for (const estado of document.querySelectorAll('select[data-localidades]')) {
    const cidade = estado.form.elements.cidade;
    const aviso = document.createElement('small');
    aviso.setAttribute('role', 'status');
    cidade.after(aviso);
    let consulta;
    estado.addEventListener('change', async () => {
        cidade.replaceChildren(new Option('Selecione o município', ''));
        aviso.textContent = '';
        cidade.disabled = true;
        if (!estado.value) {
            cidade.disabled = false;
            return;
        }
        try {
            consulta ??= fetch(estado.dataset.localidades).then(response => {
                if (!response.ok) throw new Error('Falha ao carregar localidades');
                return response.json();
            });
            const dados = await consulta;
            cidade.replaceChildren(new Option('Selecione o município', ''),
                ...(dados[estado.value]?.municipios ?? []).map(nome => new Option(nome, nome)));
        } catch {
            consulta = undefined;
            aviso.textContent = 'Não foi possível carregar os municípios. Selecione o estado novamente.';
        } finally {
            cidade.disabled = false;
        }
    });
}
