from django import forms

from .models import Societa


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
