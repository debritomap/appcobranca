from django.core.management.base import BaseCommand
from alunos.models import Dia

class Command(BaseCommand):
    help = 'Cria automaticamente os 31 dias do mês na tabela Dia'

    def handle(self, *args, **options):
        for i in range(0, 31):
            dia, criado = Dia.objects.get_or_create(dia=i)
            if criado:
                self.stdout.write(self.style.SUCCESS(f'Dia {i} criado com sucesso!'))
            else:
                self.stdout.write(f'Dia {i} já existia.')
        
        self.stdout.write(self.style.SUCCESS('Todos os 31 dias foram criados!'))