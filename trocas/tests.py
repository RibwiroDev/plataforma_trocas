from django.test import TestCase
from django.urls import reverse

from contas.models import Usuario
from catalogo.models import Categoria, Item
from .models import Avaliacao, Mensagem, Proposta


class TrocasTestsBase(TestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nome='Categoria Teste')
        self.ana = Usuario.objects.create_user(username='ana', password='Senha123!')
        self.bruno = Usuario.objects.create_user(username='bruno', password='Senha123!')
        self.item_ana = Item.objects.create(moderacao=Item.Moderacao.APROVADO, dono=self.ana, titulo='Item Ana', descricao='x', categoria=self.categoria)
        self.item_bruno = Item.objects.create(moderacao=Item.Moderacao.APROVADO, dono=self.bruno, titulo='Item Bruno', descricao='x', categoria=self.categoria)

    def propor(self, usuario_cliente, item_desejado, item_ofertado, mensagem='quero trocar'):
        return usuario_cliente.post(reverse('propor_troca', args=[item_desejado.pk]), {
            'item_ofertado': item_ofertado.id, 'mensagem': mensagem,
        })


class PropostaTests(TrocasTestsBase):
    def test_nao_pode_propor_pelo_proprio_item(self):
        self.client.login(username='ana', password='Senha123!')
        response = self.propor(self.client, self.item_ana, self.item_ana)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Proposta.objects.exists())

    def test_propor_cria_proposta_pendente_e_muda_item_pra_em_negociacao(self):
        self.client.login(username='bruno', password='Senha123!')
        response = self.propor(self.client, self.item_ana, self.item_bruno)
        self.assertEqual(response.status_code, 302)

        proposta = Proposta.objects.get(item_desejado=self.item_ana, item_ofertado=self.item_bruno)
        self.assertEqual(proposta.status, Proposta.Status.PENDENTE)

        self.item_ana.refresh_from_db()
        self.assertEqual(self.item_ana.status, Item.Status.EM_NEGOCIACAO)

    def test_propostas_concorrentes_so_libera_item_quando_todas_resolvidas(self):
        carla = Usuario.objects.create_user(username='carla', password='Senha123!')
        item_carla = Item.objects.create(moderacao=Item.Moderacao.APROVADO, dono=carla, titulo='Item Carla', descricao='x', categoria=self.categoria)

        self.client.login(username='bruno', password='Senha123!')
        self.propor(self.client, self.item_ana, self.item_bruno)
        self.client.logout()

        self.client.login(username='carla', password='Senha123!')
        self.propor(self.client, self.item_ana, item_carla)
        self.client.logout()

        proposta_bruno = Proposta.objects.get(proponente=self.bruno)
        proposta_carla = Proposta.objects.get(proponente=carla)

        self.client.login(username='ana', password='Senha123!')
        self.client.post(reverse('recusar_proposta', args=[proposta_bruno.pk]))
        self.item_ana.refresh_from_db()
        self.assertEqual(self.item_ana.status, Item.Status.EM_NEGOCIACAO, 'ainda tem a proposta da Carla pendente')

        self.client.post(reverse('recusar_proposta', args=[proposta_carla.pk]))
        self.item_ana.refresh_from_db()
        self.assertEqual(self.item_ana.status, Item.Status.DISPONIVEL, 'não há mais nenhuma proposta pendente')


class AceitarPropostaTests(TrocasTestsBase):
    def setUp(self):
        super().setUp()
        self.client.login(username='bruno', password='Senha123!')
        self.propor(self.client, self.item_ana, self.item_bruno)
        self.proposta = Proposta.objects.get(item_desejado=self.item_ana, item_ofertado=self.item_bruno)
        self.client.logout()

    def test_apenas_dono_do_item_desejado_aceita(self):
        self.client.login(username='bruno', password='Senha123!')
        response = self.client.post(reverse('aceitar_proposta', args=[self.proposta.pk]))
        self.assertEqual(response.status_code, 404)

    def test_aceitar_marca_os_dois_itens_como_trocados(self):
        self.client.login(username='ana', password='Senha123!')
        self.client.post(reverse('aceitar_proposta', args=[self.proposta.pk]))

        self.item_ana.refresh_from_db()
        self.item_bruno.refresh_from_db()
        self.assertEqual(self.item_ana.status, Item.Status.TROCADO)
        self.assertEqual(self.item_bruno.status, Item.Status.TROCADO)

    def test_aceitar_recusa_automaticamente_outras_propostas_conflitantes(self):
        carla = Usuario.objects.create_user(username='carla', password='Senha123!')
        item_carla = Item.objects.create(moderacao=Item.Moderacao.APROVADO, dono=carla, titulo='Item Carla', descricao='x', categoria=self.categoria)
        self.client.login(username='carla', password='Senha123!')
        self.propor(self.client, self.item_ana, item_carla)
        proposta_carla = Proposta.objects.get(proponente=carla)
        self.client.logout()

        self.client.login(username='ana', password='Senha123!')
        self.client.post(reverse('aceitar_proposta', args=[self.proposta.pk]))

        proposta_carla.refresh_from_db()
        self.assertEqual(proposta_carla.status, Proposta.Status.RECUSADA)

    def test_item_trocado_some_do_catalogo(self):
        self.client.login(username='ana', password='Senha123!')
        self.client.post(reverse('aceitar_proposta', args=[self.proposta.pk]))
        response = self.client.get(reverse('lista_itens'))
        self.assertNotContains(response, 'Item Ana')


class AvaliacaoTests(TrocasTestsBase):
    def setUp(self):
        super().setUp()
        self.client.login(username='bruno', password='Senha123!')
        self.propor(self.client, self.item_ana, self.item_bruno)
        self.proposta = Proposta.objects.get(item_desejado=self.item_ana, item_ofertado=self.item_bruno)
        self.client.logout()

    def test_nao_pode_avaliar_proposta_ainda_pendente(self):
        self.client.login(username='ana', password='Senha123!')
        response = self.client.get(reverse('avaliar_troca', args=[self.proposta.pk]))
        self.assertEqual(response.status_code, 404)

    def test_usuario_de_fora_nao_pode_avaliar(self):
        self.client.login(username='ana', password='Senha123!')
        self.client.post(reverse('aceitar_proposta', args=[self.proposta.pk]))
        self.client.logout()

        carla = Usuario.objects.create_user(username='carla', password='Senha123!')
        self.client.login(username='carla', password='Senha123!')
        response = self.client.get(reverse('avaliar_troca', args=[self.proposta.pk]))
        self.assertEqual(response.status_code, 404)

    def test_avaliacao_recalcula_reputacao_e_bloqueia_duplicata(self):
        self.client.login(username='ana', password='Senha123!')
        self.client.post(reverse('aceitar_proposta', args=[self.proposta.pk]))

        response = self.client.post(reverse('avaliar_troca', args=[self.proposta.pk]), {
            'nota': 5, 'comentario': 'Ótima troca!',
        })
        self.assertEqual(response.status_code, 302)

        self.bruno.refresh_from_db()
        self.assertEqual(str(self.bruno.reputacao_media), '5.00')

        # tenta avaliar de novo a mesma troca
        self.client.post(reverse('avaliar_troca', args=[self.proposta.pk]), {'nota': 1, 'comentario': 'de novo'})
        self.assertEqual(Avaliacao.objects.filter(proposta=self.proposta, avaliador=self.ana).count(), 1)


class ChatTests(TrocasTestsBase):
    def setUp(self):
        super().setUp()
        self.client.login(username='bruno', password='Senha123!')
        self.propor(self.client, self.item_ana, self.item_bruno)
        self.proposta = Proposta.objects.get(item_desejado=self.item_ana, item_ofertado=self.item_bruno)
        self.client.logout()

    def test_usuario_de_fora_nao_acessa_a_conversa(self):
        carla = Usuario.objects.create_user(username='carla', password='Senha123!')
        self.client.login(username='carla', password='Senha123!')
        response = self.client.get(reverse('conversa', args=[self.proposta.pk]))
        self.assertEqual(response.status_code, 404)

    def test_participante_envia_e_outro_recebe(self):
        self.client.login(username='bruno', password='Senha123!')
        self.client.post(reverse('conversa', args=[self.proposta.pk]), {'texto': 'Oi, topa trocar?'})
        self.client.logout()

        self.client.login(username='ana', password='Senha123!')
        response = self.client.get(reverse('conversa', args=[self.proposta.pk]))
        self.assertContains(response, 'Oi, topa trocar?')

    def test_mensagem_marcada_como_lida_ao_ser_vista(self):
        self.client.login(username='bruno', password='Senha123!')
        self.client.post(reverse('conversa', args=[self.proposta.pk]), {'texto': 'Oi!'})
        self.client.logout()

        self.client.login(username='ana', password='Senha123!')
        self.client.get(reverse('conversa', args=[self.proposta.pk]))

        mensagem = Mensagem.objects.get(texto='Oi!')
        self.assertTrue(mensagem.lida)

    def test_chat_continua_liberado_apos_proposta_aceita(self):
        self.client.login(username='ana', password='Senha123!')
        self.client.post(reverse('aceitar_proposta', args=[self.proposta.pk]))
        response = self.client.post(reverse('conversa', args=[self.proposta.pk]), {'texto': 'Combinamos a entrega?'})
        self.assertEqual(response.status_code, 302)

    def test_badge_de_nao_lidas_aparece_na_listagem(self):
        self.client.login(username='bruno', password='Senha123!')
        self.client.post(reverse('conversa', args=[self.proposta.pk]), {'texto': 'Mensagem 1'})
        self.client.post(reverse('conversa', args=[self.proposta.pk]), {'texto': 'Mensagem 2'})
        self.client.logout()

        self.client.login(username='ana', password='Senha123!')
        response = self.client.get(reverse('propostas_recebidas'))
        self.assertContains(response, 'chat-badge')
        self.assertContains(response, '>2<')


class StatusPresoTests(TrocasTestsBase):
    def test_item_oferecido_em_duas_propostas_nao_deixa_o_outro_preso(self):
        carla = Usuario.objects.create_user(username='carla', password='Senha123!')
        item_carla = Item.objects.create(moderacao=Item.Moderacao.APROVADO, dono=carla, titulo='Item Carla', descricao='x', categoria=self.categoria)

        self.client.login(username='bruno', password='Senha123!')
        self.propor(self.client, self.item_ana, self.item_bruno)
        self.propor(self.client, item_carla, self.item_bruno)  # mesmo item oferecido duas vezes
        self.client.logout()

        proposta_ana = Proposta.objects.get(item_desejado=self.item_ana)
        self.client.login(username='ana', password='Senha123!')
        self.client.post(reverse('aceitar_proposta', args=[proposta_ana.pk]))

        item_carla.refresh_from_db()
        self.assertEqual(item_carla.status, Item.Status.DISPONIVEL)

    def test_excluir_item_oferecido_libera_o_item_desejado(self):
        self.client.login(username='bruno', password='Senha123!')
        self.propor(self.client, self.item_ana, self.item_bruno)
        self.client.post(reverse('excluir_item', args=[self.item_bruno.pk]))

        self.item_ana.refresh_from_db()
        self.assertEqual(self.item_ana.status, Item.Status.DISPONIVEL)


class ChatRobustezTests(TrocasTestsBase):
    def setUp(self):
        super().setUp()
        self.proposta = Proposta.objects.create(
            item_desejado=self.item_ana, item_ofertado=self.item_bruno, proponente=self.bruno
        )
        self.client.login(username='ana', password='Senha123!')

    def test_polling_com_parametro_invalido_nao_derruba(self):
        response = self.client.get(reverse('mensagens_novas', args=[self.proposta.pk]), {'desde': 'abc'})
        self.assertEqual(response.status_code, 200)

    def test_mensagem_acima_do_limite_e_rejeitada(self):
        self.client.post(reverse('conversa', args=[self.proposta.pk]), {'texto': 'a' * 5000})
        self.assertEqual(Mensagem.objects.count(), 0)
