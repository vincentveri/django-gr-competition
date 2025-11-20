from django.shortcuts import render, redirect

from .models import Societa

def lista_societa(request):
    societa = Societa.objects.all()
    return render(request, 'anagrafiche/lista_societa.html', {'societa_list': societa})


def crea_societa(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        codice_fiscale = request.POST.get('codice_fiscale')
        nuova_societa = Societa(nome=nome, codice_fiscale=codice_fiscale)
        nuova_societa.save()
        return redirect('lista_societa')
    return render(request, 'anagrafiche/crea_societa.html')