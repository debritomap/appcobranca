# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import Http404
from django.contrib.auth.backends import ModelBackend
from django.core.cache import cache
import uuid, re, os, logging
from .forms import LoginForm
from .models import Mensalidade # ReguaCobranca, Aluno

# Configurar logger
logger = logging.getLogger(__name__)

class RateLimitedBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Limitar tentativas por IP
        ip = request.META.get('REMOTE_ADDR', '')
        cache_key = f"login_attempts_{ip}_{username}"
        login_attempts = cache.get(cache_key, 0)
        
        # Bloquear após 5 tentativas por 15 minutos
        if login_attempts >= 5:
            logger.warning(f"Muitas tentativas de login para {username} do IP {ip}")
            return None
        
        # Autenticar normalmente
        user = super().authenticate(request, username=username, password=password, **kwargs)
        
        if user is None:
            # Incrementar contador de tentativas
            cache.set(cache_key, login_attempts + 1, 60*15)  # 15 minutos
            logger.warning(f"Falha de login para {username} do IP {ip}")
        else:
            # Limpar contador em caso de sucesso
            cache.delete(cache_key)
            
        return user

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            whatsapp = form.cleaned_data['whatsapp']
            password = form.cleaned_data['password']
            
            # Sanitizar input
            whatsapp = re.sub(r'\D', '', whatsapp)  # Remover não-dígitos
            
            # Limitar tamanho da senha para evitar ataques de hash
            if len(password) > 100:
                messages.error(request, 'Senha inválida')
                return redirect('login')
                
            user = authenticate(request, whatsapp=whatsapp, password=password)
            if user is not None:
                if not user.is_active:
                    messages.error(request, 'Esta conta está desativada')
                    logger.warning(f"Tentativa de login em conta desativada: {whatsapp}")
                    return redirect('login')
                    
                auth_login(request, user)
                request.session['aluno_id'] = user.id
                request.session.set_expiry(3600)  # Expirar sessão após 1 hora
                logger.info(f"Login bem-sucedido: {user.username}")
                return redirect('area_logada')
            else:
                messages.error(request, 'Credenciais inválidas')
                return redirect('login')
    else:
        form = LoginForm()
    
    return render(request, 'index.html', {'form': form})

@login_required
def area_logada(request):
    aluno = request.user
    mensalidades = Mensalidade.objects.filter(aluno=aluno)
    
    return render(request, 'aluno.html', {
        'aluno': aluno,
        'mensalidades': mensalidades
    })

@login_required
@require_POST  # Garante que só aceitamos requisições POST
def upload_comprovante(request, mensalidade_id):
    if not request.FILES.get('comprovante'):
        messages.warning(request, 'Nenhum arquivo enviado.')
        return redirect('area_logada')
        
    try:
        # Garantir que o aluno só acesse suas próprias mensalidades
        mensalidade = get_object_or_404(Mensalidade, id=mensalidade_id, aluno=request.user)
        
        # Validar tipo de arquivo
        arquivo = request.FILES['comprovante']
        nome_arquivo = arquivo.name.lower()
        if not (nome_arquivo.endswith('.pdf') or nome_arquivo.endswith('.jpg') or 
                nome_arquivo.endswith('.jpeg') or nome_arquivo.endswith('.png')):
            messages.error(request, 'Tipo de arquivo não permitido. Use PDF, JPG, JPEG ou PNG.')
            return redirect('area_logada')
            
        # Limitar tamanho do arquivo (5MB)
        if arquivo.size > 5 * 1024 * 1024:
            messages.error(request, 'Arquivo muito grande. O tamanho máximo é 5MB.')
            return redirect('area_logada')

        # Excluir comprovante anterior se existir
        if mensalidade.comprovante and os.path.isfile(mensalidade.comprovante.path):
            os.remove(mensalidade.comprovante.path)

        # Gerar nome de arquivo seguro
        ext = nome_arquivo.split('.')[-1]
        novo_nome = f"{uuid.uuid4()}.{ext}"

        # Salvar arquivo
        mensalidade.comprovante.save(novo_nome, arquivo)
        mensalidade.save()
        
        logger.info(f"Comprovante enviado: mensalidade {mensalidade_id} por {request.user.username}")
        messages.success(request, 'Comprovante enviado com sucesso!')
    except Mensalidade.DoesNotExist:
        logger.warning(f"Tentativa de acesso não autorizado: mensalidade {mensalidade_id} por {request.user.username}")
        raise Http404("Mensalidade não encontrada")
    except Exception as e:
        logger.error(f"Erro ao processar comprovante: {str(e)}")
        messages.error(request, 'Ocorreu um erro ao processar o arquivo.')

    return redirect('area_logada')

@login_required
def logout_view(request):
    logger.info(f"Logout: {request.user.username}")
    logout(request)
    request.session.flush()
    return redirect('login')

def normalize_number(number):
    # Sanitizar entrada
    if not isinstance(number, str):
        return ""
    return re.sub(r'\D', '', number)


def terms_of_use_view(request):
    return render(request, 'terms_of_use.html')