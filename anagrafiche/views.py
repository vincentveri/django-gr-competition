from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AccountForm, RegistrazioneSocietaForm, AtletaForm, AtletaFormSet, AttrezzoForm, esercizio_formset_class, SocietaForm
from .models import Atleta, Attrezzo, Profilo, Societa


def societa_utente(user):
    """The società the logged-in user belongs to (None if they have no profile)."""
    profilo = getattr(user, 'profilo', None)
    return profilo.societa if profilo else None


def societa_visibili(user):
    if user.is_superuser:
        return Societa.objects.all()
    societa = societa_utente(user)
    return Societa.objects.filter(pk=societa.pk) if societa else Societa.objects.none()


def atleti_visibili(user):
    """Athletes the user may see: only those of their own società (superusers see all)."""
    if user.is_superuser:
        return Atleta.objects.all()
    societa = societa_utente(user)
    return Atleta.objects.filter(societa=societa) if societa else Atleta.objects.none()


def societa_per_form(user):
    """The società to force on new/edited athletes (None lets superusers choose)."""
    return None if user.is_superuser else societa_utente(user)


@login_required
def lista_societa(request):
    societa = societa_visibili(request.user)
    return render(request, 'anagrafiche/lista_societa.html', {'societa_list': societa})


@login_required
def crea_societa(request):
    # A società is created at registration; creating extra ones here is for superusers only.
    if not request.user.is_superuser:
        raise PermissionDenied
    form = SocietaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('lista_societa')
    return render(request, 'anagrafiche/crea_societa.html', {'form': form})


@login_required
def lista_atleti(request):
    atleti = atleti_visibili(request.user).select_related('societa', 'categoria')
    return render(request, 'anagrafiche/lista_atleti.html', {'atleti_list': atleti})


@login_required
def crea_atleta(request):
    form = AtletaForm(request.POST or None, societa=societa_per_form(request.user))
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('lista_atleti')
    return render(request, 'anagrafiche/crea_atleta.html', {'form': form})


@login_required
def dettaglio_atleta(request, pk):
    atleta = get_object_or_404(atleti_visibili(request.user), pk=pk)

    # One blank exercise row for each apparatus not yet assigned to this athlete.
    libere = Attrezzo.objects.exclude(esercizi__atleta=atleta).count()
    FormSet = esercizio_formset_class(extra=libere)

    # The page holds two independent forms, told apart by the submit button's "azione" value.
    azione = request.POST.get('azione') if request.method == 'POST' else None

    if azione == 'atleta':
        form = AtletaForm(request.POST, instance=atleta, societa=societa_per_form(request.user))
        if form.is_valid():
            form.save()
            messages.success(request, "Dati atleta salvati.")
            return redirect('dettaglio_atleta', pk=atleta.pk)
    else:
        form = AtletaForm(instance=atleta, societa=societa_per_form(request.user))

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


@login_required
def lista_attrezzi(request):
    attrezzi = Attrezzo.objects.order_by('nome')
    return render(request, 'anagrafiche/lista_attrezzi.html', {'attrezzi_list': attrezzi})


@login_required
def crea_attrezzo(request):
    form = AttrezzoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('lista_attrezzi')
    return render(request, 'anagrafiche/crea_attrezzo.html', {'form': form})


@login_required
def crea_atleti_multipli(request):
    queryset = Atleta.objects.none()
    form_kwargs = {'societa': societa_per_form(request.user)}
    if request.method == 'POST':
        formset = AtletaFormSet(request.POST, queryset=queryset, prefix='atleti', form_kwargs=form_kwargs)
        if formset.is_valid():
            salvati = formset.save()
            messages.success(request, f"{len(salvati)} atleti salvati.")
            return redirect('lista_atleti')
    else:
        formset = AtletaFormSet(queryset=queryset, prefix='atleti', form_kwargs=form_kwargs)
    return render(request, 'anagrafiche/crea_atleti_multipli.html', {
        'formset': formset,
        'mostra_societa': form_kwargs['societa'] is None,
    })


def registrazione(request):
    if request.user.is_authenticated:
        return redirect('lista_atleti')

    account_form = AccountForm(request.POST or None, prefix='account')
    societa_form = RegistrazioneSocietaForm(request.POST or None, prefix='societa')

    if request.method == 'POST' and account_form.is_valid() and societa_form.is_valid():
        # Create the user, its società and the link between them together, or not at all.
        with transaction.atomic():
            utente = account_form.save()
            societa = societa_form.save(commit=False)
            societa.email = utente.email  # same email as the account
            societa.save()
            Profilo.objects.create(utente=utente, societa=societa)
        login(request, utente)
        messages.success(request, "Registrazione completata.")
        return redirect('lista_atleti')

    return render(request, 'anagrafiche/registrazione.html', {
        'account_form': account_form,
        'societa_form': societa_form,
    })
