from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('area/', views.area_logada, name='area_logada'),
    path('logout/', views.logout_view, name='logout'),
    path('upload_comprovante/<int:mensalidade_id>/', views.upload_comprovante, name='upload_comprovante'),
    # Adicione esta nova rota para login via token
    path('login/<str:token>/', views.auto_login, name='auto_login'),
]