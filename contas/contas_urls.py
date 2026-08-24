from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    path('cadastro/', views.cadastro, name='cadastro'),
    path('perfil/', views.perfil, name='perfil'),
    path('login/', LoginView.as_view(template_name='contas/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]