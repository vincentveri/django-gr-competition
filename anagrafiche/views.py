from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AtletaForm, AtletaFormSet, AttrezzoForm, esercizio_formset_class, SocietaForm
from .models import Atleta, Attrezzo, Societa

def lista_societa(request):
    societa = Societa.objects.all()
    return render(request, 'anagrafiche/lista_societa.html', {'societa_list': societa})


def crea_societa(request):
    form = SocietaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('lista_societa')
    return render(request, 'anagrafiche/crea_societa.html', {'form': form})


def lista_atleti(request):
    atleti = Atleta.objects.select_related('societa', 'categoria')
    return render(request, 'anagrafiche/lista_atleti.html', {'atleti_list': atleti})


def crea_atleta(request):
    form = AtletaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('lista_atleti')
    return render(request, 'anagrafiche/crea_atleta.html', {'form': form})


def dettaglio_atleta(request, pk):
    atleta = get_object_or_404(Atleta, pk=pk)

    # One blank exercise row for each apparatus not yet assigned to this athlete.
    libere = Attrezzo.objects.exclude(esercizi__atleta=atleta).count()
    FormSet = esercizio_formset_class(extra=libere)

    # The page holds two independent forms, told apart by the submit button's "azione" value.
    azione = request.POST.get('azione') if request.method == 'POST' else None

    if azione == 'atleta':
        form = AtletaForm(request.POST, instance=atleta)
        if form.is_valid():
            form.save()
            messages.success(request, "Dati atleta salvati.")
            return redirect('dettaglio_atleta', pk=atleta.pk)
    else:
        form = AtletaForm(instance=atleta)

    if azione == 'esercizi':
        formset = FormSet(request.POST, request.FILES, instance=atleta)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Esercizi salvati.")
            return redirect('dettaglio_atleta', pk=atleta.pk)
    else:
        formset = FormSet(instance=atleta)

    return render(request, 'anagrafiche/dettaglio_atleta.html', {
        'atleta': atleta,
        'form': form,
        'formset': formset,
    })


def lista_attrezzi(request):
    attrezzi = Attrezzo.objects.order_by('nome')
    return render(request, 'anagrafiche/lista_attrezzi.html', {'attrezzi_list': attrezzi})


def crea_attrezzo(request):
    form = AttrezzoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('lista_attrezzi')
    return render(request, 'anagrafiche/crea_attrezzo.html', {'form': form})


def crea_atleti_multipli(request):
    queryset = Atleta.objects.none()
    if request.method == 'POST':
        formset = AtletaFormSet(request.POST, queryset=queryset, prefix='atleti')
        if formset.is_valid():
            salvati = formset.save()
            messages.success(request, f"{len(salvati)} atleti salvati.")
            return redirect('lista_atleti')
    else:
        formset = AtletaFormSet(queryset=queryset, prefix='atleti')
    return render(request, 'anagrafiche/crea_atleti_multipli.html', {'formset': formset})
