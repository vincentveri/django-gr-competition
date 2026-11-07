from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import AccessoForm

urlpatterns = [
    path('accedi/', auth_views.LoginView.as_view(
        template_name='anagrafiche/accedi.html',
        authentication_form=AccessoForm,
        redirect_authenticated_user=True,
    ), name='login'),
    path('esci/', auth_views.LogoutView.as_view(), name='logout'),
    path('registrazione/', views.registrazione, name='registrazione'),
    path('societa/', views.lista_societa, name='lista_societa'),
    path('societa/nuova/', views.crea_societa, name='crea_societa'),
    path('atleti/', views.lista_atleti, name='lista_atleti'),
    path('atleti/multiplo/', views.crea_atleti_multipli, name='crea_atleti_multipli'),
    path('atleti/<int:pk>/', views.dettaglio_atleta, name='dettaglio_atleta'),
    path('atleti/nuovo/', views.crea_atleta, name='crea_atleta'),
    path('attrezzi/', views.lista_attrezzi, name='lista_attrezzi'),
    path('attrezzi/nuovo/', views.crea_attrezzo, name='crea_attrezzo'),
]
