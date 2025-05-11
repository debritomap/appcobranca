from celery import shared_task
from alunos.models import Mensalidade, ReguaCobranca
from datetime import datetime, timedelta
from pathlib import Path
import environ, os, re, requests, pika
import logging
from django.core.signing import TimestampSigner

# Configuração de logging
logger = logging.getLogger(__name__)

# Configurações centralizadas
def _get_env_variable(var_name):
  env = environ.Env()
  BASE_DIR = Path(__file__).resolve().parent.parent
  environ.Env.read_env(os.path.join(BASE_DIR, '.env'))
  return env(var_name)

# Variáveis de ambiente carregadas uma vez
RABBIT_HOST = _get_env_variable("RABBIT_HOST")
RABBIT_QUEUE = _get_env_variable("RABBIT_QUEUE")
WHATSAPP_URL = _get_env_variable("WHATSAPP_URL")
WHATSAPP_TOKEN = _get_env_variable("WHATSAPP_TOKEN")
WHATSAPP_TEMPLATE_NAME = _get_env_variable("WHATSAPP_TEMPLATE_NAME")
WHATSAPP_LANGUAGE_CODE = _get_env_variable("LANGUAGE_CODE")
DOMINIO_SITE = _get_env_variable("DOMINIO_SITE")

@shared_task
def execute_billing_reminder():
  """Executa a régua de cobrança para mensalidades pendentes"""
  logger.info("Iniciando execução da régua de cobrança")
  print(f"Iniciando execução da régua de cobrança")
  contador = 0
  
  try:
    # Buscar mensalidades ativas e ainda não pagas
    mensalidades = Mensalidade.objects.exclude(status__in=['pago', 'comprovante_enviado', 'inativo'])
    
    for mensalidade in mensalidades:
      for regua in ReguaCobranca.objects.all():
        vencimento = mensalidade.data_vencimento
        dias_antes = timedelta(days=regua.dia_cobranca.dia)
        hoje = datetime.now().date()
        
        if (hoje == vencimento - dias_antes) or (hoje > vencimento):
          print(f"hoje == vencimento - dias_antes: #{hoje == vencimento - dias_antes}")
          print(f"hoje > vencimento: #{hoje > vencimento}")
          _enqueue_billing_alert(mensalidade.pk)
          contador += 1
                
    logger.info(f"Régua de cobrança executada com sucesso. {contador} mensagens enfileiradas.")
    print(f"Régua de cobrança executada: {contador} mensagens")
  except Exception as e:
    logger.error(f"Erro ao executar régua de cobrança: {str(e)}")

def _enqueue_billing_alert(mensalidade_id: int):
  """Enfileira uma mensalidade para cobrança no RabbitMQ"""
  try:
    # Uso de context manager para gerenciar conexão
    with pika.BlockingConnection(pika.URLParameters(RABBIT_HOST)) as connection:
      channel = connection.channel()
      channel.queue_declare(queue=RABBIT_QUEUE, durable=True)
      channel.basic_publish(
        exchange='', 
        routing_key=RABBIT_QUEUE, 
        body=str(mensalidade_id)
      )
    logger.info(f"Mensalidade {mensalidade_id} enfileirada com sucesso")
    print(f"Mensalidade {mensalidade_id} enfileirada com sucesso")
  except Exception as e:
    logger.error(f"Erro ao enfileirar mensalidade {mensalidade_id}: {str(e)}")
    print(f"Erro ao enfileirar mensalidade {mensalidade_id}: {str(e)}")
    raise

# Função de consumo mais robusta
@shared_task(bind=True)
def consume_messages(self):
    """Consome mensagens da fila do RabbitMQ"""
    logger.info("Iniciando consumo de mensagens de cobrança")
    print("Iniciando consumo de mensagens de cobrança")
    try:
        # Usar URLParameters com a string de conexão do ambiente
        parameters = pika.URLParameters(RABBIT_HOST)
        
        # Configurações adicionais se necessário
        parameters.heartbeat = 600
        parameters.blocked_connection_timeout = 300
        
        with pika.BlockingConnection(parameters) as connection:
            channel = connection.channel()
            channel.queue_declare(queue=RABBIT_QUEUE, durable=True)
            channel.basic_consume(
                queue=RABBIT_QUEUE, 
                on_message_callback=callback, 
                auto_ack=True
            )
            logger.info("Aguardando mensagens. Para sair pressione CTRL+C")
            print("Aguardando mensagens. Para sair pressione CTRL+C")
            # Este método bloqueia até que o canal seja fechado
            channel.start_consuming()
    except KeyboardInterrupt:
        print("Consumo de mensagens interrompido pelo usuário")
        logger.info("Consumo de mensagens interrompido pelo usuário")
    except Exception as e:
        print(f"Erro no consumo de mensagens: {str(e)}")
        logger.error(f"Erro no consumo de mensagens: {str(e)}")
        self.retry(countdown=60, max_retries=None)

def callback(ch, method, properties, body):
  """Callback chamado quando uma mensagem é recebida"""
  try:
    mensalidade_id = body.decode('utf-8')
    logger.info(f"Mensagem recebida para a mensalidade {mensalidade_id}")
    print(f"Mensagem recebida para a mensalidade {mensalidade_id}")
    _send_whatsapp_template(pk=mensalidade_id)
  except Exception as e:
    print(f"Erro ao processar mensagem: {str(e)}")
    logger.error(f"Erro ao processar mensagem: {str(e)}")

def _send_whatsapp_template(pk: str):
  """Envia mensagem WhatsApp usando template"""
  headers = {
    "Authorization": f"Bearer {WHATSAPP_TOKEN}",
    "Content-Type": "application/json"
  }
  
  try:
    mensalidade = Mensalidade.objects.get(pk=pk)
    data = _data(mensalidade)
    response = requests.post(WHATSAPP_URL, headers=headers, json=data)
    
    if response.status_code >= 200 and response.status_code < 300:
      logger.info(f"Mensagem enviada com sucesso para {mensalidade.aluno.whatsapp}")
      print(f"Mensagem enviada com sucesso para {mensalidade.aluno.whatsapp}")
    else:
      logger.error(f"Erro no envio: {response.status_code} - {response.text}") 
      print(f"Erro no envio: {response.status_code} - {response.text}")
    return response
  except Mensalidade.DoesNotExist:
    logger.error(f"Mensalidade com ID {pk} não encontrada.")
    print(f"Mensalidade com ID {pk} não encontrada.")
    return None
  except Exception as e:
    logger.error(f"Erro ao enviar mensagem: {str(e)}")
    print(f"Erro ao enviar mensagem: {str(e)}")
    return None

def _billing_message(mensalidade: Mensalidade):
  """Formata mensagem de cobrança conforme status da mensalidade"""
  billing_due_day = mensalidade.data_vencimento.day
  current_day = datetime.now().day
  delta = billing_due_day - current_day
  
  if delta < 0:
    return f"está em atraso desde o dia {billing_due_day}. Pedimos que regularize o quanto antes"
  elif delta == 0:
    return "vence hoje"
  else:
    return f"vence em {delta} dia(s), com vencimento previsto para o dia {billing_due_day}"

def _normalize_whatsapp_number(whatsapp_number: str):
  """Normaliza número de WhatsApp para formato internacional"""
  phone_number = re.sub(r'\D', '', whatsapp_number)
  
  # Número completo com código do Brasil
  if len(phone_number) == 13 and phone_number.startswith('55'):
    return phone_number
  
  # Número brasileiro sem código do país (11 dígitos = DDD + 9 dígitos)
  elif len(phone_number) == 11:
    # Se já começar com 55, retorna como está
    if phone_number.startswith('55'):
      return phone_number
    # Caso comum no Brasil: DDD + 9 + 8 dígitos
    else:
      return '55' + phone_number
      
  # Outros formatos comuns
  elif len(phone_number) == 10:
    # Formato antigo no Brasil: DDD + 8 dígitos
    return '55' + phone_number
  elif len(phone_number) == 9 and phone_number.startswith('9'):
    # Apenas os 9 dígitos sem DDD (assumindo DDD 11-SP)
    return '5511' + phone_number
  elif len(phone_number) == 8:
    # Apenas os 8 dígitos sem 9 e sem DDD (assumindo DDD 11-SP)
    return '5511' + '9' + phone_number
  else:
    # Log do erro mas use um formato padrão em vez de falhar
    logger.warning(f"Formato de número não reconhecido: {whatsapp_number}, tentando usar como está")
    print(f"Formato de número não reconhecido: {whatsapp_number}, tentando usar como está")
    # Em vez de falhar, tente usar o número como está ou com 55 na frente
    return '55' + phone_number if not phone_number.startswith('55') else phone_number

def format_parameters(variables: list):
  """Formata parâmetros para o template WhatsApp"""
  parameters = []
  for variable in variables:
    parameters.append({"type": "text", "text": variable})
  return parameters

def _data(mensalidade: Mensalidade):
    phone_number = "55" + re.sub(r'\D', '', mensalidade.aluno.whatsapp)
    language_code = _get_env_variable("LANGUAGE_CODE")

    return {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "template",
        "template": {
            "name": _get_env_variable("WHATSAPP_TEMPLATE_NAME"),
            "language": { "code": language_code },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        { "type": "text", "text": mensalidade.aluno.username },
                        { "type": "text", "text": f"{mensalidade.valor:.2f}" },
                        { "type": "text", "text": _billing_message(mensalidade) },
                        { "type": "text", "text": _get_env_variable("DOMINIO_SITE") },
                        { "type": "text", "text": mensalidade.aluno.password },
                    ]
                }
            ]
        }
    }

# def _data(mensalidade: Mensalidade):
#   """Prepara dados para envio da mensagem WhatsApp"""
#   # Gerar token seguro para acesso
#   signer = TimestampSigner()
#   token = signer.sign(str(mensalidade.aluno.id))
#   login_url = f"{DOMINIO_SITE}login/{token}/"
#   whatsapp = _normalize_whatsapp_number(mensalidade.aluno.whatsapp)
#   return {
#     "messaging_product": "whatsapp",
#     "to": whatsapp,
#     "type": "template",
#     "template": {
#       "name": WHATSAPP_TEMPLATE_NAME,
#       "language": {"code": WHATSAPP_LANGUAGE_CODE},
#       "components": [
#         {
#           "type": "body", 
#           "parameters": format_parameters([
#             mensalidade.aluno.username,
#             f"R$ {mensalidade.valor:.2f}",
#             _billing_message(mensalidade),
#             login_url  # Link seguro em vez de senha
#           ])
#         }
#       ]
#     }
#   }