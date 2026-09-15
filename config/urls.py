from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('contas.urls')),
    path('', include('catalogo.urls')),
    path('', include('trocas.urls')),
]
