# Visual do SWAP no site

Aplique as pastas deste pacote sobre o repositório plataforma_trocas, preservando a estrutura. Revise o diff e faça commit em uma branch de prévia. Quando a prévia estiver validada, faça merge na branch de produção configurada na Vercel. O pacote contém templates e estáticos. O deploy deve continuar usando as configurações de Django, MySQL e Cloudinary já cadastradas.

O APK SWAP Online acessa https://plataforma-trocas.vercel.app/ por HTTPS. Enquanto o site servir o layout anterior, o APK aplica o tema no aparelho. Quando o layout novo estiver publicado, ele usa o layout servido pelo Django.

## Descrição de anúncios

Ao digitar o título, o formulário mostra um rascunho que o usuário pode inserir e editar. Para habilitar a geração real, configure OPENAI_API_KEY e OPENAI_DESCRIPTION_MODEL nas variáveis de ambiente do projeto Vercel e faça novo deploy. Use um modelo da conta compatível com a Responses API. A chave permanece no servidor. A geração envia somente o título do item ao provedor quando o usuário toca em Gerar com IA. A integração foi testada com uma resposta simulada da API.

Este pacote já inclui as listas de estados e municípios e as alterações de visual. A localização por anúncio exige aplicar a migração catalogo.0004_localidade_item no banco de produção. O APK online continua usando o endereço público do site.

## Explorar por estado e navegação

O filtro combina a UF do anúncio (ou a do anunciante, quando o anúncio não tem UF própria) com categoria e conserva os dois na paginação. A barra inferior troca somente o conteúdo das telas principais e consulta o servidor a cada toque. Telas com formulário enviado, sessão expirada ou conversa mantêm a navegação normal.

## Localização do anúncio

Antes de promover esta versão em produção, aplique `python manage.py migrate` em um ambiente com as mesmas variáveis de banco do projeto Vercel. Os campos novos começam em branco nos registros existentes. O APK SWAP Online 2.6 mostra Usar minha localização quando a tela apresenta os campos Estado e Município. O Android sugere o município e a UF, e o usuário revisa antes de salvar. O Django recebe somente esses campos, sem as coordenadas.

## Moderação de anúncios

Aplique também a migração catalogo.0005_moderacao antes de promover o deploy. Os anúncios existentes entram como pendentes. Em /admin/, abra Catálogo > Itens e use o filtro Pendente. Abra o anúncio para conferir as fotos, altere o estado para Aprovado ou Reprovado e salve. Informe o motivo quando reprovar. O dono acompanha a decisão no Perfil.

As novas fotos ficam no banco e são servidas pelo Django com controle de acesso. URLs antigas já emitidas pelo Cloudinary continuam sujeitas às regras do próprio Cloudinary.

## Menu Administração

Aplique as migrações antes de publicar, incluindo catalogo.0006_permissao_moderacao. Em um ambiente Django ligado ao banco de produção, execute python manage.py conceder_moderacao NOME_DE_USUARIO --email EMAIL_DA_CONTA. Use a conta já cadastrada. O comando habilita o menu Administração e concede apenas a permissão de moderação, sem acesso de superusuário.
