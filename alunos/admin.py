from django.contrib import admin
from .models import Aluno, Mensalidade, ReguaCobranca
import re

class AlunoAdmin(admin.ModelAdmin):

  list_display = (
    "username",
    "whatsapp",
    "is_staff",
    "contrato",
    "status_contrato",
    "preço",
    "dia_vencimento",
    "is_active"
  )
  #list_filter = ("username", "whatsapp", "is_active")
  
  
  def whatsapp_formatado(self, obj):
    phone_number = re.sub(r'\D', '', obj.whatsapp)
    numero = ''.join(filter(str.isdigit, phone_number or ""))
    if len(numero) == 11:
      return f"({numero[:2]}) {numero[2:7]}-{numero[7:]}"
    return phone_number

  whatsapp_formatado.short_description = "WhatsApp"  

# Register your models here.
admin.site.register(Aluno, AlunoAdmin)
admin.site.register(Mensalidade)
admin.site.register(ReguaCobranca)
