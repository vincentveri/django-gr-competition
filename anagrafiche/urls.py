from django.urls import path

from . import views

urlpatterns = [
    path('societa/', views.lista_societa, name='lista_societa'),
    path('societa/nuova/', views.crea_societa, name='crea_societa'),
]