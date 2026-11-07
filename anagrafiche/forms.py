from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.forms import BaseInlineFormSet, BaseModelFormSet, inlineformset_factory, modelformset_factory

from .models import Atleta, Attrezzo, Esercizio, Societa


EMPTY_LABEL = "-- Seleziona"


class SocietaForm(forms.ModelForm):
    class Meta:
        model = Societa
        fields = [
            "nome",
            "codice_fiscale",
            "partita_iva",
            "indirizzo",
            "numero_civico",
            "citta",
            "cap",
            "telefono",
            "email",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input"

        self.fields['numero_civico'].label = "N.Civico"


class AtletaForm(forms.ModelForm):
    class Meta:
        model = Atleta
        fields = [
            "nome",
            "cognome",
            "anno_nascita",
            "email",
            "societa",
            "categoria",
            "fascia",
            "livello",
        ]
        labels = {
            "anno_nascita": "Anno di nascita",
            "societa": "Società",
        }

    def __init__(self, *args, societa=None, **kwargs):
        # When a società is given, the athlete always belongs to it and the field is not offered.
        super().__init__(*args, **kwargs)
        if societa is not None:
            del self.fields["societa"]
            self.instance.societa = societa
        for field in self.fields.values():
            field.widget.attrs["class"] = "input"

        for nome in ("societa", "categoria", "fascia", "livello"):
            if nome in self.fields:
                self.fields[nome].empty_label = EMPTY_LABEL


class EsercizioForm(forms.ModelForm):
    class Meta:
        model = Esercizio
        fields = ["attrezzo", "audio"]
        labels = {"attrezzo": "Attrezzo", "audio": "File audio"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["attrezzo"].widget.attrs["class"] = "input"
        self.fields["attrezzo"].empty_label = EMPTY_LABEL
        self.fields["audio"].widget.attrs.update({
            "class": "input",
            "accept": ".mp3,.wav,.m4a,.ogg,audio/*",
        })

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("attrezzo") and not cleaned.get("audio"):
            self.add_error("audio", "Il file audio è obbligatorio per l'attrezzo selezionato.")
        return cleaned


class BaseEsercizioFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        visti = set()
        for form in self.forms:
            if not hasattr(form, "cleaned_data") or form.cleaned_data.get("DELETE"):
                continue
            attrezzo = form.cleaned_data.get("attrezzo")
            if attrezzo is None:
                continue
            if attrezzo.pk in visti:
                raise forms.ValidationError(
                    f"L'attrezzo “{attrezzo}” è stato selezionato più volte: ogni attrezzo può essere definito una sola volta."
                )
            visti.add(attrezzo.pk)

        if any(form.errors for form in self.forms):
            return
        if not visti:
            raise forms.ValidationError("Devi caricare almeno un esercizio (attrezzo con file audio).")


def esercizio_formset_class(extra):
    return inlineformset_factory(
        Atleta,
        Esercizio,
        form=EsercizioForm,
        formset=BaseEsercizioFormSet,
        extra=extra,
        can_delete=True,
    )


class AttrezzoForm(forms.ModelForm):
    class Meta:
        model = Attrezzo
        fields = ["nome"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nome"].widget.attrs["class"] = "input"


class BaseAtletaFormSet(BaseModelFormSet):
    def clean(self):
        super().clean()
        if any(form.errors for form in self.forms):
            return
        if not any(form.has_changed() for form in self.forms):
            raise forms.ValidationError("Inserisci almeno un atleta.")


AtletaFormSet = modelformset_factory(
    Atleta,
    form=AtletaForm,
    formset=BaseAtletaFormSet,
    extra=5,
)


class AccessoForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input"
        self.fields["username"].label = "Nome utente"
        self.fields["password"].label = "Password"


class AccountForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input"
        self.fields["username"].label = "Nome utente"
        self.fields["email"].label = "Email account"
        self.fields["email"].required = True
        self.fields["password1"].label = "Password"
        self.fields["password2"].label = "Conferma password"
