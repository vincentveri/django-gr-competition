from django.contrib import admin

from .models import Attrezzo, Categoria, Livello, Societa
from .models import Atleta, Competizione, Fascia
    

admin.site.register(Attrezzo)
admin.site.register(Categoria)
admin.site.register(Livello)
admin.site.register(Societa)
admin.site.register(Atleta)
admin.site.register(Competizione)
admin.site.register(Fascia)