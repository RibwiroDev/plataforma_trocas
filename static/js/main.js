document.addEventListener('DOMContentLoaded', function () {
  addPasswordToggles();
  addAvatarPreview();
  addSubmitLoadingState();
});

/* ---------- 1. Mostrar/ocultar senha ---------- */
function addPasswordToggles() {
  var passwordInputs = document.querySelectorAll('input[type="password"]');

  passwordInputs.forEach(function (input) {
    var wrapper = document.createElement('div');
    wrapper.className = 'password-field';
    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);

    var toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'password-toggle';
    toggle.setAttribute('aria-label', 'Mostrar senha');
    toggle.innerHTML = eyeIcon(false);

    toggle.addEventListener('click', function () {
      var showing = input.type === 'text';
      input.type = showing ? 'password' : 'text';
      toggle.innerHTML = eyeIcon(!showing);
      toggle.setAttribute('aria-label', showing ? 'Mostrar senha' : 'Ocultar senha');
    });

    wrapper.appendChild(toggle);
  });
}

function eyeIcon(open) {
  if (open) {
    return '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.94 10.94 0 0 1 12 20c-7 0-10-8-10-8a18.6 18.6 0 0 1 4.22-5.94M9.9 4.24A10.94 10.94 0 0 1 12 4c7 0 10 8 10 8a18.6 18.6 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';
  }
  return '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s3-8 11-8 11 8 11 8-3 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
}

/* ---------- 2. Preview da foto de perfil ---------- */
function addAvatarPreview() {
  var fileInput = document.querySelector('input[type="file"][name="foto_perfil"]');
  if (!fileInput) return;

  var previewBox = document.querySelector('.avatar-preview');
  if (!previewBox) return;

  fileInput.addEventListener('change', function () {
    var file = fileInput.files[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      alert('Escolha um arquivo de imagem para a foto de perfil.');
      fileInput.value = '';
      return;
    }

    var reader = new FileReader();
    reader.onload = function (event) {
      previewBox.innerHTML = '<img src="' + event.target.result + '" alt="Pré-visualização da foto de perfil">';
    };
    reader.readAsDataURL(file);
  });
}

/* ---------- 3. Estado de carregamento ao enviar o formulário ---------- */
function addSubmitLoadingState() {
  var forms = document.querySelectorAll('form.styled-form');

  forms.forEach(function (form) {
    form.addEventListener('submit', function () {
      var button = form.querySelector('button[type="submit"]');
      if (!button || button.disabled) return;

      button.dataset.originalText = button.textContent;
      button.disabled = true;
      button.innerHTML = '<span class="spinner" aria-hidden="true"></span>Enviando…';
    });
  });
}
