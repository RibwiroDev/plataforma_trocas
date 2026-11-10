from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = 'Concede acesso restrito à fila de moderação para uma conta existente.'

    def add_arguments(self, parser):
        parser.add_argument('usuario')
        parser.add_argument('--email', required=True)

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        try:
            usuario = User.objects.select_for_update().get(
                username=options['usuario'], email__iexact=options['email'],
            )
        except (User.DoesNotExist, User.MultipleObjectsReturned) as error:
            raise CommandError('Nenhuma conta única corresponde ao nome de usuário e e-mail.') from error
        if not usuario.is_active:
            raise CommandError('A conta está inativa.')
        permissao = Permission.objects.get(content_type__app_label='catalogo', codename='moderar_item')
        usuario.is_staff = True
        usuario.save(update_fields=['is_staff'])
        usuario.user_permissions.add(permissao)
        self.stdout.write(self.style.SUCCESS(f'Moderação ativada para {usuario.username}.'))
