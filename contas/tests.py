from django.test import TestCase
from django.urls import reverse

from .models import Usuario


class CadastroTests(TestCase):
    def test_cadastro_cria_usuario_e_loga_automaticamente(self):
        response = self.client.post(reverse('cadastro'), {
            'username': 'novato',
            'email': 'novato@teste.com',
            'password1': 'SenhaForte123!',
            'password2': 'SenhaForte123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Usuario.objects.filter(username='novato').exists())
        # já loga automaticamente após o cadastro
        response = self.client.get(reverse('perfil'))
        self.assertEqual(response.status_code, 200)

    def test_cadastro_bloqueia_email_duplicado(self):
        Usuario.objects.create_user(username='existente', email='mesmo@teste.com', password='Senha123!')
        response = self.client.post(reverse('cadastro'), {
            'username': 'outrouser',
            'email': 'mesmo@teste.com',
            'password1': 'SenhaForte123!',
            'password2': 'SenhaForte123!',
        })
        self.assertEqual(response.status_code, 200)  # form volta com erro, não redireciona
        self.assertFalse(Usuario.objects.filter(username='outrouser').exists())


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(username='maria', password='SenhaForte123!')

    def test_login_com_credenciais_corretas(self):
        response = self.client.post(reverse('login'), {'username': 'maria', 'password': 'SenhaForte123!'})
        self.assertEqual(response.status_code, 302)

    def test_login_com_senha_errada_nao_autentica(self):
        response = self.client.post(reverse('login'), {'username': 'maria', 'password': 'errada'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_so_aceita_post(self):
        self.client.login(username='maria', password='SenhaForte123!')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 405)

    def test_logout_via_post_funciona(self):
        self.client.login(username='maria', password='SenhaForte123!')
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class PerfilTests(TestCase):
    def test_perfil_exige_login(self):
        response = self.client.get(reverse('perfil'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_perfil_acessivel_quando_logado(self):
        Usuario.objects.create_user(username='ana', password='Senha123!')
        self.client.login(username='ana', password='Senha123!')
        response = self.client.get(reverse('perfil'))
        self.assertEqual(response.status_code, 200)


class PerfilPublicoTests(TestCase):
    def test_perfil_publico_nao_exige_login(self):
        Usuario.objects.create_user(username='bruno', password='Senha123!')
        response = self.client.get(reverse('perfil_publico', args=['bruno']))
        self.assertEqual(response.status_code, 200)

    def test_perfil_publico_de_usuario_inexistente_da_404(self):
        response = self.client.get(reverse('perfil_publico', args=['nao-existe']))
        self.assertEqual(response.status_code, 404)

    def test_perfil_publico_mostra_reputacao_zerada_por_padrao(self):
        Usuario.objects.create_user(username='carla', password='Senha123!')
        response = self.client.get(reverse('perfil_publico', args=['carla']))
        self.assertContains(response, 'Ainda não recebeu avaliações')

class LocalidadeTests(TestCase):
    def test_cadastro_exibe_listas_e_carrega_script(self):
        response = self.client.get(reverse('cadastro'))
        self.assertContains(response, 'data-localidades=')
        self.assertContains(response, 'contas/localidades.js')
        self.assertContains(response, '<option value="AM">Amazonas</option>', html=True)

    def test_cadastro_salva_municipio_da_uf(self):
        response = self.client.post(reverse('cadastro'), {
            'username': 'localidade', 'email': 'localidade@example.test',
            'password1': 'SenhaForte123!', 'password2': 'SenhaForte123!',
            'estado': 'AM', 'cidade': 'Manaus',
        })
        self.assertRedirects(response, reverse('perfil'))
        self.assertTrue(Usuario.objects.filter(username='localidade', estado='AM', cidade='Manaus').exists())

    def test_perfil_rejeita_cidade_inventada_ou_de_outra_uf(self):
        usuario = Usuario.objects.create_user(username='moradora', estado='AM', cidade='Manaus')
        self.client.force_login(usuario)
        for cidade in ('Cidade Inventada', 'Belém'):
            with self.subTest(cidade=cidade):
                response = self.client.post(reverse('perfil'), {
                    'username': usuario.username, 'estado': 'AM', 'cidade': cidade,
                })
                self.assertFormError(response.context['form'], 'cidade', 'Selecione um município do estado informado.')
                usuario.refresh_from_db()
                self.assertEqual(usuario.cidade, 'Manaus')

    def test_perfil_preserva_localidade_antiga_e_aceita_correcao(self):
        usuario = Usuario.objects.create_user(username='morador', estado='AM', cidade='Manáus')
        self.client.force_login(usuario)
        self.assertContains(self.client.get(reverse('perfil')), 'Manáus')
        for cidade in ('Manáus', 'Manaus'):
            response = self.client.post(reverse('perfil'), {
                'username': usuario.username, 'estado': 'AM', 'cidade': cidade,
            })
            self.assertRedirects(response, reverse('perfil'))
            usuario.refresh_from_db()
            self.assertEqual(usuario.cidade, cidade)
