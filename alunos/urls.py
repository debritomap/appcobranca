from django.urls import path
from . import views
from .views import terms_of_use_view

urlpatterns = [
    path('', views.login_view, name='login'),
    path('area/', views.area_logada, name='area_logada'),
    path('logout/', views.logout_view, name='logout'),
    path('upload_comprovante/<int:mensalidade_id>/', views.upload_comprovante, name='upload_comprovante'),
    path('termos-de-uso/', terms_of_use_view, name='terms_of_use'),
]