from django.urls import path

from . import views

urlpatterns = [
    path('societa/', views.lista_societa, name='lista_societa'),
    path('societa/nuova/', views.crea_societa, name='crea_societa'),
    path('atleti/', views.lista_atleti, name='lista_atleti'),
    path('atleti/multiplo/', views.crea_atleti_multipli, name='crea_atleti_multipli'),
    path('atleti/<int:pk>/', views.dettaglio_atleta, name='dettaglio_atleta'),
    path('atleti/nuovo/', views.crea_atleta, name='crea_atleta'),
    path('attrezzi/', views.lista_attrezzi, name='lista_attrezzi'),
    path('attrezzi/nuovo/', views.crea_attrezzo, name='crea_attrezzo'),
]
