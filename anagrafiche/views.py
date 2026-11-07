from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AccountForm, RegistrazioneSocietaForm, AtletaForm, AtletaFormSet, AttrezzoForm, esercizio_formset_class, esercizio_squadra_formset_class, SocietaForm, SquadraForm
from django.forms import modelformset_factory

from .models import Atleta, Attrezzo, EsercizioSquadra, Profilo, Societa, Squadra


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



def squadre_visibili(user):
    if user.is_superuser:
        return Squadra.objects.all()
    societa = societa_utente(user)
    return Squadra.objects.filter(societa=societa) if societa else Squadra.objects.none()


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
    atleti = atleti_visibili(request.user).select_related('categoria', 'fascia', 'livello').prefetch_related('esercizi')
    attrezzi = list(Attrezzo.objects.filter(tipo=Attrezzo.TIPO_ATLETA).order_by('nome'))

    # One row per athlete; for each apparatus a boolean: does the athlete have that exercise?
    righe = []
    for atleta in atleti:
        assegnati = {e.attrezzo_id for e in atleta.esercizi.all()}
        righe.append({'atleta': atleta, 'flags': [a.pk in assegnati for a in attrezzi]})

    return render(request, 'anagrafiche/lista_atleti.html', {
        'atleti_list': atleti,
        'righe': righe,
        'attrezzi': attrezzi,
    })


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
    libere = Attrezzo.objects.filter(tipo=Attrezzo.TIPO_ATLETA).exclude(esercizi__atleta=atleta).count()
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
def dettaglio_squadra(request, pk):
    squadra = get_object_or_404(squadre_visibili(request.user), pk=pk)

    # One blank row for each apparatus not yet assigned to this squadra.
    libere = Attrezzo.objects.filter(tipo=Attrezzo.TIPO_SQUADRA).exclude(esercizi_squadra__squadra=squadra).count()
    FormSet = esercizio_squadra_formset_class(extra=libere)

    if request.method == 'POST':
        formset = FormSet(request.POST, request.FILES, instance=squadra)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Esercizi della squadra salvati.")
            return redirect('dettaglio_squadra', pk=squadra.pk)
    else:
        formset = FormSet(instance=squadra)
    return render(request, 'anagrafiche/dettaglio_squadra.html', {'squadra': squadra, 'formset': formset})


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


@login_required
def lista_squadre(request):
    squadre = squadre_visibili(request.user).select_related('societa', 'categoria').prefetch_related('atleti')
    return render(request, 'anagrafiche/lista_squadre.html', {'squadre_list': squadre})


@login_required
def crea_squadra(request):
    """Single form: squadra details, existing own athletes (searchable) and new athletes on the fly."""
    user = request.user
    societa_fissa = societa_per_form(user)
    NuoviFormSet = modelformset_factory(Atleta, form=AtletaForm, extra=3)
    erroreAtleti = None

    if request.method == 'POST':
        squadra_form = SquadraForm(request.POST, societa=societa_fissa)
        societa = None
        if squadra_form.is_valid():
            societa = societa_fissa or squadra_form.cleaned_data['societa']
        nuovi_formset = NuoviFormSet(
            request.POST, queryset=Atleta.objects.none(), prefix='nuovi',
            form_kwargs={'societa': societa},
        )
        ids = request.POST.getlist('atleti')
        esistenti = atleti_visibili(user).filter(pk__in=[i for i in ids if i.isdigit()]) if ids else Atleta.objects.none()
        if ids and esistenti.count() != len(set(ids)):
            erroreAtleti = "Uno o più atleti selezionati non sono validi."

        if squadra_form.is_valid() and nuovi_formset.is_valid() and not erroreAtleti:
            nuovi = [f for f in nuovi_formset.forms if f.has_changed()]
            if not esistenti.exists() and not nuovi:
                erroreAtleti = "Seleziona almeno un atleta o inseriscine uno nuovo."
            else:
                with transaction.atomic():
                    squadra = squadra_form.save(commit=False)
                    squadra.societa = societa
                    squadra.save()
                    atleti_nuovi = nuovi_formset.save()
                    squadra.atleti.add(*esistenti, *atleti_nuovi)
                messages.success(request, f"Squadra \u201c{squadra.nome}\u201d creata.")
                return redirect('lista_squadre')
    else:
        squadra_form = SquadraForm(societa=societa_fissa)
        nuovi_formset = NuoviFormSet(queryset=Atleta.objects.none(), prefix='nuovi',
                                     form_kwargs={'societa': societa_fissa})
        ids = []

    atleti_disponibili = atleti_visibili(user).select_related('societa').order_by('cognome', 'nome')
    return render(request, 'anagrafiche/crea_squadra.html', {
        'squadra_form': squadra_form,
        'nuovi_formset': nuovi_formset,
        'atleti_disponibili': atleti_disponibili,
        'selezionati': {int(i) for i in ids if i.isdigit()},
        'errore_atleti': erroreAtleti,
        'mostra_societa': societa_fissa is None,
    })
