from django.test import TestCase
from django.urls import reverse

from contas.models import Usuario
from .models import Categoria, Item, ItemImagem

class SeedCategoriasTests(TestCase):
    def test_categorias_iniciais_sao_criadas_pela_migration(self):
        self.assertEqual(Categoria.objects.count(), 9)
        self.assertTrue(Categoria.objects.filter(nome='Eletrônicos').exists())


class CatalogoTestsBase(TestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nome='Categoria Teste')
        self.ana = Usuario.objects.create_user(username='ana', password='Senha123!')
        self.bruno = Usuario.objects.create_user(username='bruno', password='Senha123!')


class ListaItensTests(CatalogoTestsBase):
    def test_lista_mostra_itens_disponiveis(self):
        Item.objects.create(moderacao=Item.Moderacao.APROVADO, dono=self.ana, titulo='Item Disponível', descricao='x', categoria=self.categoria)
        response = self.client.get(reverse('lista_itens'))
        self.assertContains(response, 'Item Disponível')

    def test_lista_nao_mostra_itens_trocados(self):
        Item.objects.create(
            moderacao=Item.Moderacao.APROVADO,
            dono=self.ana, titulo='Item Trocado', descricao='x',
            categoria=self.categoria, status=Item.Status.TROCADO,
        )
        response = self.client.get(reverse('lista_itens'))
        self.assertNotContains(response, 'Item Trocado')

    def test_lista_mostra_itens_em_negociacao(self):
        Item.objects.create(
            moderacao=Item.Moderacao.APROVADO,
            dono=self.ana, titulo='Item Negociando', descricao='x',
            categoria=self.categoria, status=Item.Status.EM_NEGOCIACAO,
        )
        response = self.client.get(reverse('lista_itens'))
        self.assertContains(response, 'Item Negociando')

    def test_filtro_por_categoria(self):
        outra = Categoria.objects.create(nome='Outra Categoria')
        Item.objects.create(moderacao=Item.Moderacao.APROVADO, dono=self.ana, titulo='ItemA', descricao='x', categoria=self.categoria)
        Item.objects.create(moderacao=Item.Moderacao.APROVADO, dono=self.ana, titulo='ItemB', descricao='x', categoria=outra)

        response = self.client.get(reverse('lista_itens'), {'categoria': outra.id})
        self.assertContains(response, 'ItemB')
        self.assertNotContains(response, 'ItemA')


class CriarItemTests(CatalogoTestsBase):
    def test_criar_item_exige_login(self):
        response = self.client.get(reverse('criar_item'))
        self.assertEqual(response.status_code, 302)

    def test_criar_item_logado_funciona(self):
        self.client.login(username='ana', password='Senha123!')
        response = self.client.post(reverse('criar_item'), {
            'titulo': 'Novo item',
            'descricao': 'Descrição qualquer',
            'categoria': self.categoria.id,
            'estado_conservacao': 'usado',
            'aceita_categoria': '',
            'aceita_descricao_livre': 'qualquer coisa',
        })
        self.assertEqual(response.status_code, 302)
        item = Item.objects.get(titulo='Novo item')
        self.assertEqual(item.dono, self.ana)
        self.assertEqual(item.status, Item.Status.DISPONIVEL)


class EditarExcluirItemTests(CatalogoTestsBase):
    def setUp(self):
        super().setUp()
        self.item = Item.objects.create(moderacao=Item.Moderacao.APROVADO, dono=self.ana, titulo='Item da Ana', descricao='x', categoria=self.categoria)

    def test_dono_consegue_acessar_edicao(self):
        self.client.login(username='ana', password='Senha123!')
        response = self.client.get(reverse('editar_item', args=[self.item.pk]))
        self.assertEqual(response.status_code, 200)

    def test_outro_usuario_nao_consegue_editar(self):
        self.client.login(username='bruno', password='Senha123!')
        response = self.client.get(reverse('editar_item', args=[self.item.pk]))
        self.assertEqual(response.status_code, 404)

    def test_outro_usuario_nao_consegue_excluir(self):
        self.client.login(username='bruno', password='Senha123!')
        response = self.client.post(reverse('excluir_item', args=[self.item.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Item.objects.filter(pk=self.item.pk).exists())

    def test_dono_consegue_excluir(self):
        self.client.login(username='ana', password='Senha123!')
        response = self.client.post(reverse('excluir_item', args=[self.item.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Item.objects.filter(pk=self.item.pk).exists())


class RobustezEDesempenhoTests(CatalogoTestsBase):
    def test_categoria_invalida_na_url_nao_derruba_a_pagina(self):
        response = self.client.get(reverse('lista_itens'), {'categoria': 'abc'})
        self.assertEqual(response.status_code, 200)

    def test_home_nao_faz_uma_consulta_por_item(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        from .models import ItemImagem

        for i in range(12):
            item = Item.objects.create(moderacao=Item.Moderacao.APROVADO, dono=self.ana, titulo=f'Item {i}', descricao='x', categoria=self.categoria)
            ItemImagem.objects.create(item=item, imagem=f'itens/{i}-a.jpg', principal=True)
            ItemImagem.objects.create(item=item, imagem=f'itens/{i}-b.jpg', principal=False)

        with CaptureQueriesContext(connection) as consultas:
            response = self.client.get(reverse('lista_itens'))
        self.assertEqual(response.status_code, 200)
        print('\nQUERIES home (12 itens, 2 fotos cada):', len(consultas))
        self.assertLessEqual(len(consultas), 6, 'a home voltou a fazer consultas por item (N+1)')

class SugestaoDescricaoTests(TestCase):
    def setUp(self):
        from django.core.cache import cache

        cache.clear()
        self.url = reverse('sugerir_descricao')

    def test_exige_login_e_post(self):
        self.assertEqual(self.client.post(self.url, {'titulo': 'Livro'}).status_code, 302)
        self.client.force_login(Usuario.objects.create_user(username='sugestao'))
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assertEqual(self.client.post(self.url, {'titulo': '  '}).status_code, 400)

    def test_sem_chave_informa_que_ia_indisponivel(self):
        from unittest.mock import patch

        self.client.force_login(Usuario.objects.create_user(username='sugestao'))
        with patch.dict('os.environ', {'OPENAI_API_KEY': '', 'OPENAI_DESCRIPTION_MODEL': ''}):
            response = self.client.post(self.url, {'titulo': 'Livro'})
        self.assertEqual(response.status_code, 503)

    def test_extrai_texto_e_limita_pedidos_consecutivos(self):
        from io import BytesIO
        from unittest.mock import patch

        self.client.force_login(Usuario.objects.create_user(username='sugestao'))
        body = b'{"output":[{"type":"message","content":[{"type":"output_text","text":"Livro disponivel para troca."}]}]}'
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'chave-de-teste', 'OPENAI_DESCRIPTION_MODEL': 'modelo-teste'}):
            with patch('catalogo.descricao.urlopen', return_value=BytesIO(body)) as enviar:
                response = self.client.post(self.url, {'titulo': 'Livro'})
                self.assertEqual(response.json(), {'descricao': 'Livro disponivel para troca.'})
                self.assertEqual(self.client.post(self.url, {'titulo': 'Livro'}).status_code, 429)
                enviar.assert_called_once()

class RegiaoCatalogoTests(TestCase):
    def test_estado_filtra_itens_e_pode_ser_combinado_com_categoria(self):
        categoria = Categoria.objects.first()
        outra_categoria = Categoria.objects.exclude(pk=categoria.pk).first()
        am = Usuario.objects.create_user(username='manaus', estado='AM')
        sp = Usuario.objects.create_user(username='saopaulo', estado='SP')
        livro = Item.objects.create(moderacao=Item.Moderacao.APROVADO, dono=am, categoria=categoria, titulo='Livro em Manaus')
        Item.objects.create(moderacao=Item.Moderacao.APROVADO, dono=am, categoria=outra_categoria, titulo='Jogo em Manaus')
        Item.objects.create(moderacao=Item.Moderacao.APROVADO, dono=sp, categoria=categoria, titulo='Livro em São Paulo')

        resposta = self.client.get(reverse('lista_itens'), {'estado': 'am', 'categoria': categoria.pk})
        self.assertEqual(list(resposta.context['page_obj']), [livro])
        self.assertContains(resposta, 'value="AM" selected')
        self.assertContains(resposta, '?estado=AM')
        self.assertContains(resposta, '&amp;estado=AM')

    def test_estado_invalido_mantem_catalogo_nacional(self):
        dono = Usuario.objects.create_user(username='dona', estado='SP')
        item = Item.objects.create(moderacao=Item.Moderacao.APROVADO, dono=dono, categoria=Categoria.objects.first(), titulo='Livro')
        resposta = self.client.get(reverse('lista_itens'), {'estado': 'ZZ'})
        self.assertEqual(list(resposta.context['page_obj']), [item])
        self.assertEqual(resposta.context['estado_selecionado'], '')

class ExcluirFotoTests(TestCase):
    def setUp(self):
        self.dono = Usuario.objects.create_user(username='dono-fotos')
        self.item = Item.objects.create(moderacao=Item.Moderacao.APROVADO, dono=self.dono, titulo='Livro')
        self.foto = ItemImagem.objects.create(item=self.item, imagem='itens/capa.jpg', principal=True)
        self.outra_foto = ItemImagem.objects.create(item=self.item, imagem='itens/verso.jpg')
        self.url = reverse('remover_imagem', args=[self.foto.pk])

    def test_dono_encontra_controle_e_exclui_so_a_foto_selecionada(self):
        self.client.force_login(self.dono)
        detalhe = self.client.get(reverse('detalhe_item', args=[self.item.pk]))
        self.assertContains(detalhe, 'Gerenciar fotos')
        edicao = self.client.get(reverse('editar_item', args=[self.item.pk]))
        self.assertContains(edicao, 'Excluir foto', count=2)

        self.client.get(self.url)
        self.assertTrue(ItemImagem.objects.filter(pk=self.foto.pk).exists())
        resposta = self.client.post(self.url)
        self.assertRedirects(resposta, reverse('editar_item', args=[self.item.pk]) + '#fotos-enviadas')
        self.assertFalse(ItemImagem.objects.filter(pk=self.foto.pk).exists())
        self.outra_foto.refresh_from_db()
        self.assertTrue(self.outra_foto.principal)

    def test_outro_usuario_nao_pode_excluir_foto(self):
        self.client.force_login(Usuario.objects.create_user(username='outra-pessoa'))
        self.assertEqual(self.client.post(self.url).status_code, 404)
        self.assertTrue(ItemImagem.objects.filter(pk=self.foto.pk).exists())

class LocalidadeAnuncioTests(TestCase):
    def test_anuncio_usa_uf_propria_no_filtro_e_preserva_fallback(self):
        dono = Usuario.objects.create_user(username='regional', estado='AM', cidade='Manaus')
        categoria = Categoria.objects.first()
        self.client.force_login(dono)
        dados = {
            'titulo': 'Livro para troca', 'descricao': 'Livro usado',
            'categoria': categoria.pk, 'estado_conservacao': 'usado',
            'estado': 'SP', 'cidade': 'São Paulo',
        }
        self.assertEqual(self.client.post(reverse('criar_item'), dados).status_code, 302)
        item = Item.objects.get(dono=dono)
        self.assertEqual((item.estado, item.cidade), ('SP', 'São Paulo'))
        Item.objects.filter(pk=item.pk).update(moderacao=Item.Moderacao.APROVADO)
        antigo = Item.objects.create(moderacao=Item.Moderacao.APROVADO, dono=dono, titulo='Anúncio antigo', categoria=categoria)
        self.assertEqual(list(self.client.get(reverse('lista_itens'), {'estado': 'SP'}).context['page_obj']), [item])
        self.assertEqual(list(self.client.get(reverse('lista_itens'), {'estado': 'AM'}).context['page_obj']), [antigo])
        dados['cidade'] = 'Manaus'
        invalido = self.client.post(reverse('editar_item', args=[item.pk]), dados)
        self.assertFormError(invalido.context['form'], 'cidade', 'Selecione um município do estado informado.')
        item.refresh_from_db()
        self.assertEqual(item.cidade, 'São Paulo')

class ModeracaoAnuncioTests(CatalogoTestsBase):
    def test_foto_e_anuncio_privados_ate_aprovacao(self):
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        from PIL import Image

        imagem = BytesIO()
        Image.new('RGB', (2, 2)).save(imagem, 'PNG')
        self.client.force_login(self.ana)
        self.client.post(reverse('criar_item'), {
            'titulo': 'Anúncio para revisão',
            'descricao': 'Descrição',
            'categoria': self.categoria.pk,
            'estado_conservacao': 'usado',
            'imagens': SimpleUploadedFile('foto.png', imagem.getvalue(), 'image/png'),
        })
        item = Item.objects.get(titulo='Anúncio para revisão')
        foto = item.imagens.get()
        detalhe = reverse('detalhe_item', args=[item.pk])
        url_foto = reverse('foto_item', args=[foto.pk])
        self.assertEqual(item.moderacao, Item.Moderacao.PENDENTE)
        self.assertEqual(self.client.get(url_foto).content, imagem.getvalue())
        self.client.force_login(self.bruno)
        self.assertEqual(self.client.get(detalhe).status_code, 404)
        self.assertEqual(self.client.get(url_foto).status_code, 404)
        self.assertEqual(self.client.get(reverse('propor_troca', args=[item.pk])).status_code, 404)
        self.assertNotContains(self.client.get(reverse('lista_itens')), item.titulo)

        admin_user = Usuario.objects.create_superuser(username='moderador', password='Senha123!')
        self.client.force_login(admin_user)
        self.assertEqual(self.client.get(url_foto).status_code, 200)
        self.client.post(reverse('admin:catalogo_item_changelist'), {
            'action': 'aprovar_anuncios', '_selected_action': [item.pk],
        })
        self.client.logout()
        self.assertContains(self.client.get(detalhe), item.titulo)
        self.assertEqual(self.client.get(url_foto).status_code, 200)

        self.client.force_login(self.ana)
        self.client.post(reverse('editar_item', args=[item.pk]), {
            'titulo': 'Anúncio alterado', 'descricao': 'Nova descrição',
            'categoria': self.categoria.pk, 'estado_conservacao': 'usado',
        })
        self.client.logout()
        self.assertEqual(self.client.get(detalhe).status_code, 404)
        self.assertEqual(self.client.get(url_foto).status_code, 404)

class PainelModeradorTests(CatalogoTestsBase):
    def test_menu_restrito_e_decisoes(self):
        from django.core.management import call_command

        fila = reverse('fila_moderacao')
        item = Item.objects.create(dono=self.ana, titulo='Anúncio pendente', categoria=self.categoria)
        decidir = reverse('decidir_moderacao', args=[item.pk])
        self.client.force_login(self.bruno)
        self.assertNotContains(self.client.get(reverse('lista_itens')), 'Administração')
        self.assertEqual(self.client.get(fila).status_code, 403)
        self.assertEqual(self.client.post(decidir, {'decisao': 'aprovado'}).status_code, 403)

        self.bruno.email = 'moderador@example.test'
        self.bruno.save(update_fields=['email'])
        call_command('conceder_moderacao', self.bruno.username, email=self.bruno.email)
        self.bruno.refresh_from_db()
        self.assertFalse(self.bruno.is_superuser)
        self.assertFalse(self.bruno.has_perm('catalogo.change_item'))
        pagina = self.client.get(fila)
        self.assertContains(pagina, 'Administração')
        self.assertContains(pagina, 'Aprovar anúncio')
        self.assertContains(pagina, 'Reprovar anúncio')
        self.assertContains(pagina, item.titulo)
        self.assertEqual(self.client.get(reverse('detalhe_item', args=[item.pk])).status_code, 200)

        self.client.post(decidir, {'decisao': 'aprovado', 'revisao': 'antiga'})
        item.refresh_from_db()
        self.assertEqual(item.moderacao, Item.Moderacao.PENDENTE)
        self.client.post(decidir, {'decisao': 'reprovado', 'revisao': item.revisao_moderacao})
        item.refresh_from_db()
        self.assertEqual(item.moderacao, Item.Moderacao.PENDENTE)
        self.client.post(decidir, {'decisao': 'reprovado', 'revisao': item.revisao_moderacao, 'motivo': 'Item proibido'})
        item.refresh_from_db()
        self.assertEqual(item.moderacao, Item.Moderacao.REPROVADO)
        self.assertEqual(item.motivo_moderacao, 'Item proibido')
        novo = Item.objects.create(dono=self.ana, titulo='Outro anúncio')
        self.client.post(reverse('decidir_moderacao', args=[novo.pk]), {
            'decisao': 'aprovado', 'revisao': novo.revisao_moderacao,
        })
        novo.refresh_from_db()
        self.assertEqual(novo.moderacao, Item.Moderacao.APROVADO)
