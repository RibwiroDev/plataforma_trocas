-- ============================================================
-- SWAP — Script de criação do banco de dados (16 tabelas)
-- ============================================================
-- Gerado a partir das migrations reais do Django (contas, catalogo,
-- trocas), aplicadas contra um MariaDB 10.11 limpo (motor compatível com
-- o MySQL usado na Aiven) e extraído com SHOW CREATE TABLE.
-- Charset: utf8mb4 — igual à conexão configurada em config/settings.py.
--
-- COMO USAR (escolha UMA das formas):
--   A) python manage.py migrate        (cria as tabelas e as categorias)
--   B) carregar este script num banco vazio:
--        CREATE DATABASE swap CHARACTER SET utf8mb4;
--        mysql -u USUARIO -p swap < script_banco.sql
--      Ele também registra as migrations como aplicadas, então rodar
--      "python manage.py migrate" depois não tenta recriar nada.
-- ============================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ------------------------------------------------------------
-- Tabelas internas do Django (autenticação, sessões, admin)
-- ------------------------------------------------------------

CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `django_migrations` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `auth_group_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext DEFAULT NULL,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL CHECK (`action_flag` >= 0),
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_contas_usuario_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_contas_usuario_id` FOREIGN KEY (`user_id`) REFERENCES `contas_usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ------------------------------------------------------------
-- Domínio do projeto — app "contas"
-- ------------------------------------------------------------

CREATE TABLE `contas_usuario` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `foto_perfil` varchar(100) DEFAULT NULL,
  `telefone` varchar(20) NOT NULL,
  `cidade` varchar(100) NOT NULL,
  `estado` varchar(2) NOT NULL,
  `reputacao_media` decimal(3,2) NOT NULL,
  `criado_em` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `contas_usuario_groups` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `usuario_id` bigint(20) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `contas_usuario_groups_usuario_id_group_id_d691acec_uniq` (`usuario_id`,`group_id`),
  KEY `contas_usuario_groups_group_id_9069d15c_fk_auth_group_id` (`group_id`),
  CONSTRAINT `contas_usuario_groups_group_id_9069d15c_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `contas_usuario_groups_usuario_id_bdcd8ecf_fk_contas_usuario_id` FOREIGN KEY (`usuario_id`) REFERENCES `contas_usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `contas_usuario_user_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `usuario_id` bigint(20) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `contas_usuario_user_perm_usuario_id_permission_id_11c91988_uniq` (`usuario_id`,`permission_id`),
  KEY `contas_usuario_user__permission_id_f6e102d4_fk_auth_perm` (`permission_id`),
  CONSTRAINT `contas_usuario_user__permission_id_f6e102d4_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `contas_usuario_user__usuario_id_fd075c5d_fk_contas_us` FOREIGN KEY (`usuario_id`) REFERENCES `contas_usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ------------------------------------------------------------
-- Domínio do projeto — app "catalogo"
-- ------------------------------------------------------------

CREATE TABLE `catalogo_categoria` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `nome` varchar(80) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nome` (`nome`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `catalogo_item` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `titulo` varchar(120) NOT NULL,
  `descricao` longtext NOT NULL,
  `estado_conservacao` varchar(10) NOT NULL,
  `status` varchar(15) NOT NULL,
  `aceita_descricao_livre` varchar(200) NOT NULL,
  `criado_em` datetime(6) NOT NULL,
  `atualizado_em` datetime(6) NOT NULL,
  `aceita_categoria_id` bigint(20) DEFAULT NULL,
  `categoria_id` bigint(20) DEFAULT NULL,
  `dono_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `catalogo_item_aceita_categoria_id_4447f3cc_fk_catalogo_` (`aceita_categoria_id`),
  KEY `catalogo_item_categoria_id_ffd330ba_fk_catalogo_categoria_id` (`categoria_id`),
  KEY `catalogo_item_dono_id_72b57386_fk_contas_usuario_id` (`dono_id`),
  CONSTRAINT `catalogo_item_aceita_categoria_id_4447f3cc_fk_catalogo_` FOREIGN KEY (`aceita_categoria_id`) REFERENCES `catalogo_categoria` (`id`),
  CONSTRAINT `catalogo_item_categoria_id_ffd330ba_fk_catalogo_categoria_id` FOREIGN KEY (`categoria_id`) REFERENCES `catalogo_categoria` (`id`),
  CONSTRAINT `catalogo_item_dono_id_72b57386_fk_contas_usuario_id` FOREIGN KEY (`dono_id`) REFERENCES `contas_usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `catalogo_itemimagem` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `imagem` varchar(100) NOT NULL,
  `principal` tinyint(1) NOT NULL,
  `item_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `catalogo_itemimagem_item_id_613c6401_fk_catalogo_item_id` (`item_id`),
  CONSTRAINT `catalogo_itemimagem_item_id_613c6401_fk_catalogo_item_id` FOREIGN KEY (`item_id`) REFERENCES `catalogo_item` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ------------------------------------------------------------
-- Domínio do projeto — app "trocas"
-- ------------------------------------------------------------

CREATE TABLE `trocas_proposta` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `mensagem` longtext NOT NULL,
  `status` varchar(15) NOT NULL,
  `criado_em` datetime(6) NOT NULL,
  `atualizado_em` datetime(6) NOT NULL,
  `item_desejado_id` bigint(20) NOT NULL,
  `item_ofertado_id` bigint(20) NOT NULL,
  `proponente_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `trocas_proposta_item_desejado_id_92f6aefd_fk_catalogo_item_id` (`item_desejado_id`),
  KEY `trocas_proposta_item_ofertado_id_c942a027_fk_catalogo_item_id` (`item_ofertado_id`),
  KEY `trocas_proposta_proponente_id_a06707c0_fk_contas_usuario_id` (`proponente_id`),
  CONSTRAINT `trocas_proposta_item_desejado_id_92f6aefd_fk_catalogo_item_id` FOREIGN KEY (`item_desejado_id`) REFERENCES `catalogo_item` (`id`),
  CONSTRAINT `trocas_proposta_item_ofertado_id_c942a027_fk_catalogo_item_id` FOREIGN KEY (`item_ofertado_id`) REFERENCES `catalogo_item` (`id`),
  CONSTRAINT `trocas_proposta_proponente_id_a06707c0_fk_contas_usuario_id` FOREIGN KEY (`proponente_id`) REFERENCES `contas_usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `trocas_avaliacao` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `nota` smallint(5) unsigned NOT NULL CHECK (`nota` >= 0),
  `comentario` longtext NOT NULL,
  `criado_em` datetime(6) NOT NULL,
  `avaliado_id` bigint(20) NOT NULL,
  `avaliador_id` bigint(20) NOT NULL,
  `proposta_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uma_avaliacao_por_pessoa_por_troca` (`proposta_id`,`avaliador_id`),
  KEY `trocas_avaliacao_avaliado_id_003d796e_fk_contas_usuario_id` (`avaliado_id`),
  KEY `trocas_avaliacao_avaliador_id_148aa7eb_fk_contas_usuario_id` (`avaliador_id`),
  CONSTRAINT `trocas_avaliacao_avaliado_id_003d796e_fk_contas_usuario_id` FOREIGN KEY (`avaliado_id`) REFERENCES `contas_usuario` (`id`),
  CONSTRAINT `trocas_avaliacao_avaliador_id_148aa7eb_fk_contas_usuario_id` FOREIGN KEY (`avaliador_id`) REFERENCES `contas_usuario` (`id`),
  CONSTRAINT `trocas_avaliacao_proposta_id_748b8fb2_fk_trocas_proposta_id` FOREIGN KEY (`proposta_id`) REFERENCES `trocas_proposta` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `trocas_mensagem` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `texto` longtext NOT NULL,
  `criado_em` datetime(6) NOT NULL,
  `lida` tinyint(1) NOT NULL,
  `proposta_id` bigint(20) NOT NULL,
  `remetente_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `trocas_mensagem_proposta_id_85092dcc_fk_trocas_proposta_id` (`proposta_id`),
  KEY `trocas_mensagem_remetente_id_4b2de8de_fk_contas_usuario_id` (`remetente_id`),
  CONSTRAINT `trocas_mensagem_proposta_id_85092dcc_fk_trocas_proposta_id` FOREIGN KEY (`proposta_id`) REFERENCES `trocas_proposta` (`id`),
  CONSTRAINT `trocas_mensagem_remetente_id_4b2de8de_fk_contas_usuario_id` FOREIGN KEY (`remetente_id`) REFERENCES `contas_usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ------------------------------------------------------------
-- Dados iniciais: categorias do catálogo e registro das migrations
-- ------------------------------------------------------------

/*M!999999\- enable the sandbox mode */ 
INSERT INTO `catalogo_categoria` (`id`, `nome`) VALUES (7,'Brinquedos e Jogos'),
(5,'Eletrodomésticos'),
(1,'Eletrônicos'),
(6,'Esportes e Lazer'),
(8,'Instrumentos Musicais'),
(2,'Livros'),
(4,'Móveis'),
(9,'Outros'),
(3,'Roupas e Acessórios');
INSERT INTO `django_migrations` (`id`, `app`, `name`, `applied`) VALUES (1,'contenttypes','0001_initial','2026-10-26 21:31:33.710715'),
(2,'contenttypes','0002_remove_content_type_name','2026-10-26 21:31:33.722724'),
(3,'auth','0001_initial','2026-10-26 21:31:33.757882'),
(4,'auth','0002_alter_permission_name_max_length','2026-10-26 21:31:33.764860'),
(5,'auth','0003_alter_user_email_max_length','2026-10-26 21:31:33.768249'),
(6,'auth','0004_alter_user_username_opts','2026-10-26 21:31:33.771400'),
(7,'auth','0005_alter_user_last_login_null','2026-10-26 21:31:33.775709'),
(8,'auth','0006_require_contenttypes_0002','2026-10-26 21:31:33.776468'),
(9,'auth','0007_alter_validators_add_error_messages','2026-10-26 21:31:33.779468'),
(10,'auth','0008_alter_user_username_max_length','2026-10-26 21:31:33.782460'),
(11,'auth','0009_alter_user_last_name_max_length','2026-10-26 21:31:33.785253'),
(12,'auth','0010_alter_group_name_max_length','2026-10-26 21:31:33.790876'),
(13,'auth','0011_update_proxy_permissions','2026-10-26 21:31:33.794121'),
(14,'auth','0012_alter_user_first_name_max_length','2026-10-26 21:31:33.797092'),
(15,'contas','0001_initial','2026-10-26 21:31:33.832146'),
(16,'admin','0001_initial','2026-10-26 21:31:33.849740'),
(17,'admin','0002_logentry_remove_auto_add','2026-10-26 21:31:33.855023'),
(18,'admin','0003_logentry_add_action_flag_choices','2026-10-26 21:31:33.859629'),
(19,'catalogo','0001_initial','2026-10-26 21:31:33.881532'),
(20,'catalogo','0002_initial','2026-10-26 21:31:33.903489'),
(21,'catalogo','0003_seed_categorias','2026-10-26 21:31:33.917597'),
(22,'sessions','0001_initial','2026-10-26 21:31:33.924245'),
(23,'trocas','0001_initial','2026-10-26 21:31:33.948857'),
(24,'trocas','0002_avaliacao','2026-10-26 21:31:33.979522'),
(25,'trocas','0003_mensagem','2026-10-26 21:31:34.002469');

SET FOREIGN_KEY_CHECKS = 1;
