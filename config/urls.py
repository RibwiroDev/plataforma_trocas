from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('perfil')
    return redirect('login')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('contas.urls')),
    path('', home_redirect, name='home'),
]