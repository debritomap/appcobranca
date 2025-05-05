from django.contrib import admin
from .models import Aluno, Mensalidade, ReguaCobranca
import re

class AlunoAdmin(admin.ModelAdmin):
  def get_list_display(self, request):
    # Obter todos os campos do modelo
    all_fields = [field.name for field in self.model._meta.fields]
    # Substituir 'whatsapp' por 'whatsapp_formatado'
    fields = ['whatsapp_formatado' if f == 'whatsapp' else f for f in all_fields]
    return fields
  
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
