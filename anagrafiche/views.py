from django.shortcuts import render, redirect

from .forms import SocietaForm
from .models import Societa

def lista_societa(request):
    societa = Societa.objects.all()
    return render(request, 'anagrafiche/lista_societa.html', {'societa_list': societa})


def crea_societa(request):
    form = SocietaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('lista_societa')
    return render(request, 'anagrafiche/crea_societa.html', {'form': form})
