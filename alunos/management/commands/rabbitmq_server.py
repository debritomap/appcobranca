from django.core.management.base import BaseCommand
from alunos.tasks import consume_messages

class Command(BaseCommand):
    help = 'Inicia o servidor RabbitMQ para enviar os alertas de cobrança'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('RabbitMQ server is running...'))
        # Chamar diretamente a função para manter o processo ativo
        try:
            pass
            # Não usar .apply_async() pois isso apenas agenda a tarefa
            consume_messages()
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS('RabbitMQ server stopped'))