from django.db import migrations

CATEGORIAS_INICIAIS = [
    'Eletrônicos',
    'Livros',
    'Roupas e Acessórios',
    'Móveis',
    'Eletrodomésticos',
    'Esportes e Lazer',
    'Brinquedos e Jogos',
    'Instrumentos Musicais',
    'Outros',
]


def criar_categorias(apps, schema_editor):
    Categoria = apps.get_model('catalogo', 'Categoria')
    for nome in CATEGORIAS_INICIAIS:
        Categoria.objects.get_or_create(nome=nome)


def remover_categorias(apps, schema_editor):
    Categoria = apps.get_model('catalogo', 'Categoria')
    Categoria.objects.filter(nome__in=CATEGORIAS_INICIAIS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('catalogo', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(criar_categorias, remover_categorias),
    ]
