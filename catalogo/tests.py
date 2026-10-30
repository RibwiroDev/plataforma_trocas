from django.test import TestCase
from django.urls import reverse

from contas.models import Usuario
from .models import Categoria, Item


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
        Item.objects.create(dono=self.ana, titulo='Item Disponível', descricao='x', categoria=self.categoria)
        response = self.client.get(reverse('lista_itens'))
        self.assertContains(response, 'Item Disponível')

    def test_lista_nao_mostra_itens_trocados(self):
        Item.objects.create(
            dono=self.ana, titulo='Item Trocado', descricao='x',
            categoria=self.categoria, status=Item.Status.TROCADO,
        )
        response = self.client.get(reverse('lista_itens'))
        self.assertNotContains(response, 'Item Trocado')

    def test_lista_mostra_itens_em_negociacao(self):
        Item.objects.create(
            dono=self.ana, titulo='Item Negociando', descricao='x',
            categoria=self.categoria, status=Item.Status.EM_NEGOCIACAO,
        )
        response = self.client.get(reverse('lista_itens'))
        self.assertContains(response, 'Item Negociando')

    def test_filtro_por_categoria(self):
        outra = Categoria.objects.create(nome='Outra Categoria')
        Item.objects.create(dono=self.ana, titulo='ItemA', descricao='x', categoria=self.categoria)
        Item.objects.create(dono=self.ana, titulo='ItemB', descricao='x', categoria=outra)

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
        self.item = Item.objects.create(dono=self.ana, titulo='Item da Ana', descricao='x', categoria=self.categoria)

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
            item = Item.objects.create(dono=self.ana, titulo=f'Item {i}', descricao='x', categoria=self.categoria)
            ItemImagem.objects.create(item=item, imagem=f'itens/{i}-a.jpg', principal=True)
            ItemImagem.objects.create(item=item, imagem=f'itens/{i}-b.jpg', principal=False)

        with CaptureQueriesContext(connection) as consultas:
            response = self.client.get(reverse('lista_itens'))
        self.assertEqual(response.status_code, 200)
        print('\nQUERIES home (12 itens, 2 fotos cada):', len(consultas))
        self.assertLessEqual(len(consultas), 6, 'a home voltou a fazer consultas por item (N+1)')
