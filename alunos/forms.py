from django import forms

class LoginForm(forms.Form):
    whatsapp = forms.CharField(
        max_length=15, 
        required=True, 
        label='WhatsApp',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '(00) 00000-0000',
            'pattern': r'\(\d{2}\) \d{5}-\d{4}',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite sua senha'
        }), 
        required=True, 
        label='Senha'
    )
    
    def clean_whatsapp(self):
        """Remove caracteres não numéricos do WhatsApp"""
        whatsapp = self.cleaned_data.get('whatsapp', '')
        # Remove todos os caracteres não numéricos
        whatsapp_clean = ''.join(filter(str.isdigit, whatsapp))
        
        # Verifica se tem 11 dígitos (com DDD)
        if len(whatsapp_clean) != 11:
            raise forms.ValidationError('O WhatsApp deve ter 11 dígitos incluindo o DDD')
            
        return whatsapp_clean