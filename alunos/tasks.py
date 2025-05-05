from celery import shared_task
from alunos.models import Mensalidade, ReguaCobranca
from datetime import datetime, timedelta
from pathlib import Path
import environ, os, re, requests

@shared_task
def regua_de_cobranca():
    hoje = datetime.now().date()

    # Buscar mensalidades ativas e ainda não pagas
    mensalidades = Mensalidade.objects.exclude(status__in=['pago', 'comprovante_enviado'])

    for mensalidade in mensalidades:
        for regua in ReguaCobranca.objects.all():
            dias_antes = timedelta(days=regua.dia_cobranca.dia)
            if mensalidade.data_vencimento == hoje + (-dias_antes):
                response = send_whatsapp_template(mensalidade)
                if response.status_code == 200:
                    print(f"Mensagem enviada para {mensalidade.aluno.username} com sucesso.")
                else:
                    print(f"Erro ao enviar mensagem para {mensalidade.aluno.username}: {response.status_code} - {response.text}")
    
    return "Régua de cobrança executada com sucesso."


def send_whatsapp_template(mensalidade: Mensalidade):
    whatsapp_url = _get_env_variable("WHATSAPP_URL")
    headers = _headers()
    data = _data(mensalidade)
    response = requests.post(whatsapp_url, headers=headers, json=data)
    return response


def _get_env_variable(var_name):
    env = environ.Env()
    BASE_DIR = Path(__file__).resolve().parent.parent
    environ.Env.read_env(os.path.join(BASE_DIR, '.env'))
    return env(var_name)


def _headers():
    whatsapp_token = _get_env_variable("WHATSAPP_TOKEN")
    return {
        "Authorization": f"Bearer {whatsapp_token}",
        "Content-Type": "application/json"
    }


def _mensagem_cobranca(mensalidade: Mensalidade):
    dia_venc = mensalidade.data_vencimento.day
    hoje = datetime.now().day
    delta = dia_venc - hoje

    if delta < 0:
        return f"está em atraso desde o dia {dia_venc}. Pedimos que regularize o quanto antes"
    elif delta == 0:
        return "vence hoje"
    else:
        return f"vence em {delta} dia(s), com vencimento previsto para o dia {dia_venc}"


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
                        { "type": "text", "text": f"R$ {mensalidade.valor:.2f}" },
                        { "type": "text", "text": _mensagem_cobranca(mensalidade) },
                        { "type": "text", "text": _get_env_variable("DOMINIO_SITE") },
                        { "type": "text", "text": mensalidade.aluno.password },
                    ]
                }
            ]
        }
    }