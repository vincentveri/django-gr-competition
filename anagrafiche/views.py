from django.shortcuts import render

from .models import Societa

def lista_societa(request):
    societa = Societa.objects.all()
    return render(request, 'anagrafiche/lista_societa.html', {'societa': societa})