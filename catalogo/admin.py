from django.contrib import admin 
from .models import Categoria, Item, ItemImagem 

admin.site.register(Categoria) 
admin.site.register(Item) 
admin.site.register(ItemImagem)