from django.db import models
from django.contrib.auth.models import AbstractUser
import re

# Create your models here.
class Dia(models.Model):
    dia = models.IntegerField(choices=[
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
        (6, '6'),
        (7, '7'),
        (8, '8'),
        (9, '9'),
        (10, '10'),
        (11, '11'),
        (12, '12'),
        (13, '13'),
        (14, '14'),
        (15, '15'),
        (16, '16'),
        (17, '17'),
        (18, '18'),
        (19, '19'),
        (20, '20'),
        (21, '21'),
        (22, '22'),
        (23, '23'),
        (24, '24'),
        (25, '25'),
        (26, '26'),
        (27, '27'),
        (28, '28'),
        (29, '29'),
        (30, '30'),
        (31, '31'),
    ])

    def __str__(self):
        return str(self.dia)

class Aluno(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    whatsapp = models.CharField(max_length=15, unique=True)
    is_staff = models.BooleanField(default=False)
    contrato = models.FileField(upload_to="contratos/", null=True, blank=True)
    status_contrato = models.CharField(max_length=50, choices=[
        ('pendente', 'Pendente'),
        ('enviado', 'Enviado'),
        ('assinado', 'Assinado'),
        ('inativo', 'Inativo'),
    ], default='pendente')
    aulas_contratadas = models.IntegerField(default=0)
    aulas_realizadas = models.IntegerField(default=0)
    preço = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dia_vencimento = models.ForeignKey(Dia, on_delete=models.CASCADE, null=True)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = "whatsapp"
    REQUIRED_FIELDS = ["username", "preço", "dia_vencimento"]

    def __str__(self):
        return self.username

class Mensalidade(models.Model):
  aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE)
  data_vencimento = models.DateField()
  valor = models.DecimalField(max_digits=10, decimal_places=2)
  status = models.CharField(max_length=50, choices=[
      ('pendente', 'Pendente'),
      ('comprovante_enviado', 'Comprovante Enviado'),
      ('pago', 'Pago'),
      ('atrasado', 'Atrasado'),
      ('inativo', 'Inativo'),
  ], default='pendente')
  comprovante = models.FileField(upload_to="comprovantes/", null=True, blank=True)
  data_pagamento = models.DateField(null=True, blank=True)


  def __str__(self):
      return f"{self.aluno.username} - {self.data_vencimento} - {self.status}"
  
class ReguaCobranca(models.Model):
    dia_cobranca = models.ForeignKey(Dia, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.dia_cobranca.dia} dias antes do vencimento"