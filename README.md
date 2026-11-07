# SWAP — Plataforma de Trocas

Plataforma web para troca de itens entre pessoas (estilo OLX, mas sem dinheiro):
o usuário publica o que tem, propõe trocas pelos itens dos outros, conversa
com o outro lado da negociação e avalia a troca depois de concluída.

## Funcionalidades

- **Contas e perfil** — cadastro, login/logout, edição de perfil com foto, perfil público com reputação.
- **Catálogo** — publicar, editar e excluir itens (várias fotos por item), listagem paginada com filtro por categoria.
- **Propostas de troca** — propor, aceitar, recusar e cancelar. O item fica *disponível → em negociação → trocado* automaticamente.
- **Avaliações** — após uma troca aceita, cada lado avalia o outro (1 a 5 + comentário); a reputação média é recalculada.
- **Chat** — conversa por proposta, com atualização automática a cada 4 s e contador de mensagens não lidas.

## Tecnologias

Python · Django 6.1 · MySQL/MariaDB · Cloudinary (fotos) · Bootstrap 5 + CSS/JS próprios · python-decouple

## Requisitos

- Python 3.12 ou superior (desenvolvido em 3.14)
- MySQL 8 ou MariaDB 10.6+ (validado em MariaDB 10.11)
- No Linux, para compilar o `mysqlclient`: `sudo apt install default-libmysqlclient-dev build-essential pkg-config`
  (no Windows o `pip` já baixa um pacote pronto)

## Como executar

**1. Ambiente virtual e dependências**

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**2. Criar um banco vazio**

```sql
CREATE DATABASE swap CHARACTER SET utf8mb4;
```

**3. Configurar o `.env`**

Copie `.env.example` para `.env` e preencha (banco, `SECRET_KEY`, Cloudinary).

**4. Criar as tabelas** — escolha uma das opções:

- **A)** `python manage.py migrate` — cria as 16 tabelas e as 9 categorias iniciais.
- **B)** `mysql -u USUARIO -p swap < script_banco.sql` — mesmo resultado, direto em SQL.
  O script já registra as migrations como aplicadas, então rodar `migrate` depois não recria nada.

**5. (Opcional) Criar um administrador** para acessar `/admin/`

```bash
python manage.py createsuperuser
```

**6. Rodar**

```bash
python manage.py runserver
```

Acesse http://127.0.0.1:8000/

## Observações importantes

- **Cloudinary:** as três variáveis `CLOUDINARY_*` precisam existir para o Django iniciar.
  Para apenas avaliar o sistema, podem ter valores fictícios — tudo funciona, **exceto o upload
  de imagens** (fotos de item e de perfil), que exige credenciais reais.
- **Banco da Aiven (SSL):** se usar o banco hospedado na Aiven, coloque o certificado `ca.pem`
  na raiz do projeto, ao lado do `manage.py`. Quando o arquivo existe, a conexão usa SSL;
  sem ele, conecta normalmente num MySQL/MariaDB local.
- O `.env` e o `ca.pem` ficam fora do Git de propósito (contêm credenciais).

## Rotas principais

| Rota | O que é |
|---|---|
| `/` | Catálogo de itens (filtro `?categoria=<id>`) |
| `/cadastro/` · `/login/` · `/perfil/` | Conta do usuário |
| `/usuarios/<username>/` | Perfil público e avaliações recebidas |
| `/itens/novo/` · `/itens/<id>/` · `/itens/<id>/editar/` · `/itens/<id>/excluir/` | Itens |
| `/itens/<id>/propor/` | Propor troca por um item |
| `/propostas/recebidas/` · `/propostas/enviadas/` | Gerenciar propostas |
| `/propostas/<id>/mensagens/` | Chat da proposta |
| `/propostas/<id>/avaliar/` | Avaliar uma troca aceita |
| `/admin/` | Painel administrativo (superusuário) |

## Estrutura do projeto

```
config/     configurações do Django e rotas principais
contas/     usuário customizado, cadastro, login, perfil
catalogo/   categorias, itens, fotos
trocas/     propostas, avaliações, mensagens (chat)
templates/  base.html compartilhado
static/     css/style.css e js/main.js
script_banco.sql   DDL completo (16 tabelas) + dados iniciais
```

## Banco de dados

16 tabelas: 4 do domínio principal (`contas_usuario`, `catalogo_categoria`, `catalogo_item`,
`catalogo_itemimagem`), 3 do fluxo de troca (`trocas_proposta`, `trocas_avaliacao`,
`trocas_mensagem`) e as demais, internas do Django (autenticação, sessões, admin).

## Publicação na Vercel (opcional)

1. Ligue o banco no Aiven (Power on) e importe o repositório em vercel.com/new.
2. Em *Settings → Environment Variables*, cadastre as mesmas variáveis do `.env` e mais `DB_SSL_CA` com o conteúdo do `ca.pem` do Aiven (não envie o `ca.pem` ao GitHub).
3. A Vercel instala o `requirements.txt` (no Linux usa PyMySQL), roda o `collectstatic` e publica. As tabelas já devem existir no banco (`migrate` ou `script_banco.sql`).
