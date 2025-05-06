from django.core.management.base import BaseCommand
from alunos.models import Aluno
import os, environ
from pathlib import Path

class Command(BaseCommand):
    help = 'Cria automaticamente um usuário a partir do arquivo .env'

    def handle(self, *args, **options):
        env = environ.Env()
        BASE_DIR = Path(__file__).resolve().parent.parent
        environ.Env.read_env(os.path.join(BASE_DIR, '.env'))
        try:
          user = Aluno.objects.get(username=env('ADMIN_USERNAME'))
          user.set_password(env('ADMIN_PASSWORD'))
          user.save()
          self.stdout.write(self.style.ERROR('usuário admin já existe!'))
          self.stdout.write(self.style.SUCCESS('senha atualizada com sucesso!'))
        except Aluno.DoesNotExist:
          user = Aluno.objects.create(
            username=env('ADMIN_USERNAME'),
            whatsapp=env('ADMIN_WHATSAPP'),
            is_superuser=True,
            is_staff=True,
            is_active=True,
            preço=None,
            dia_vencimento=None,
          )
          user.set_password(env('ADMIN_PASSWORD'))
          user.save()
          self.stdout.write(self.style.SUCCESS(f'usuário admin criado com sucesso!'))