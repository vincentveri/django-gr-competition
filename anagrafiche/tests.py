from django.test import TestCase

# Create your tests here.


import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from django.contrib.auth import get_user_model

from .models import Atleta, Attrezzo, Esercizio, EsercizioSquadra, Profilo, Societa, Squadra

_MEDIA = tempfile.mkdtemp()


def login_con_societa(client, username="tester", nome="Societa Uno"):
    """Create a user with its own società and log them in. Returns the società."""
    societa = Societa.objects.create(nome=nome, codice_fiscale=f"CF-{username}", email=f"{username}@example.com")
    utente = get_user_model().objects.create_user(username, password="x")
    Profilo.objects.create(utente=utente, societa=societa)
    client.force_login(utente)
    return societa


@override_settings(MEDIA_ROOT=_MEDIA)
class DettaglioAtletaTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(_MEDIA, ignore_errors=True)

    def setUp(self):
        self.societa = login_con_societa(self.client)
        self.atleta = Atleta.objects.create(nome="Ada", cognome="Rossi", societa=self.societa)
        self.fune = Attrezzo.objects.create(nome="Fune")
        self.palla = Attrezzo.objects.create(nome="Palla")
        self.url = reverse("dettaglio_atleta", args=[self.atleta.pk])

    def _data(self, rows):
        data = {
            "azione": "esercizi",
            "esercizi-TOTAL_FORMS": len(rows),
            "esercizi-INITIAL_FORMS": 0,
            "esercizi-MIN_NUM_FORMS": 0,
            "esercizi-MAX_NUM_FORMS": 1000,
        }
        for i, (attrezzo, audio) in enumerate(rows):
            data[f"esercizi-{i}-attrezzo"] = attrezzo.pk if attrezzo else ""
            if audio:
                data[f"esercizi-{i}-audio"] = audio
        return data

    def test_page_loads_with_one_row_per_free_attrezzo(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.context["formset"].forms), 2)

    def test_saves_multiple_exercises_with_audio(self):
        data = self._data([
            (self.fune, SimpleUploadedFile("fune.mp3", b"abc", "audio/mpeg")),
            (self.palla, SimpleUploadedFile("palla.wav", b"def", "audio/wav")),
        ])
        r = self.client.post(self.url, data)
        self.assertRedirects(r, self.url)
        self.assertEqual(Esercizio.objects.filter(atleta=self.atleta).count(), 2)
        e = Esercizio.objects.get(attrezzo=self.fune)
        self.assertEqual(e.nome_file_audio, "fune.mp3")
        self.assertIn(f"esercizi/audio/{self.atleta.pk}/", e.audio.name)

    def test_duplicate_attrezzo_rejected(self):
        data = self._data([(self.fune, None), (self.fune, None)])
        r = self.client.post(self.url, data)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Esercizio.objects.count(), 0)
        self.assertTrue(r.context["formset"].non_form_errors())

    def test_invalid_extension_rejected(self):
        data = self._data([(self.fune, SimpleUploadedFile("x.exe", b"abc"))])
        r = self.client.post(self.url, data)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Esercizio.objects.count(), 0)

    def test_at_least_one_exercise_required(self):
        r = self.client.post(self.url, self._data([(None, None), (None, None)]))
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context["formset"].non_form_errors())
        self.assertEqual(Esercizio.objects.count(), 0)

    def test_attrezzo_without_audio_rejected(self):
        data = self._data([
            (self.fune, SimpleUploadedFile("fune.mp3", b"abc", "audio/mpeg")),
            (self.palla, None),
        ])
        r = self.client.post(self.url, data)
        self.assertEqual(r.status_code, 200)
        self.assertIn("audio", r.context["formset"].forms[1].errors)
        self.assertEqual(Esercizio.objects.count(), 0)

    def test_optional_rows_may_stay_blank(self):
        data = self._data([
            (self.fune, SimpleUploadedFile("fune.mp3", b"abc", "audio/mpeg")),
            (None, None),
        ])
        r = self.client.post(self.url, data)
        self.assertRedirects(r, self.url)
        self.assertEqual(Esercizio.objects.count(), 1)


class InserimentoMultiploTests(TestCase):
    url = "/atleti/multiplo/"

    def setUp(self):
        self.societa = login_con_societa(self.client)

    def _data(self, rows):
        data = {"atleti-TOTAL_FORMS": len(rows), "atleti-INITIAL_FORMS": 0,
                "atleti-MIN_NUM_FORMS": 0, "atleti-MAX_NUM_FORMS": 1000}
        for i, (nome, cognome) in enumerate(rows):
            data[f"atleti-{i}-nome"] = nome
            data[f"atleti-{i}-cognome"] = cognome
        return data

    def test_page_loads(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_saves_multiple_and_skips_blank(self):
        r = self.client.post(self.url, self._data([("Ada", "Rossi"), ("Bea", "Verdi"), ("", "")]))
        self.assertRedirects(r, "/atleti/")
        self.assertEqual(Atleta.objects.count(), 2)

    def test_partial_row_rejected(self):
        r = self.client.post(self.url, self._data([("Ada", "Rossi"), ("Bea", "")]))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Atleta.objects.count(), 0)

    def test_empty_submit_rejected(self):
        r = self.client.post(self.url, self._data([("", ""), ("", "")]))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Atleta.objects.count(), 0)


class ModificaAtletaTests(TestCase):
    def setUp(self):
        self.societa = login_con_societa(self.client)
        self.atleta = Atleta.objects.create(nome="Ada", cognome="Rossi", societa=self.societa)
        self.url = reverse("dettaglio_atleta", args=[self.atleta.pk])

    def test_page_shows_both_forms(self):
        r = self.client.get(self.url)
        self.assertEqual(r.context["form"].instance, self.atleta)
        self.assertIn("formset", r.context)

    def test_edit_athlete_only(self):
        r = self.client.post(self.url, {"azione": "atleta", "nome": "Bea", "cognome": "Verdi"})
        self.assertRedirects(r, self.url)
        self.atleta.refresh_from_db()
        self.assertEqual((self.atleta.nome, self.atleta.cognome), ("Bea", "Verdi"))
        self.assertEqual(Esercizio.objects.count(), 0)

    def test_invalid_athlete_form_shows_errors(self):
        r = self.client.post(self.url, {"azione": "atleta", "nome": "", "cognome": "Verdi"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("nome", r.context["form"].errors)
        self.assertFalse(r.context["formset"].is_bound)
        self.atleta.refresh_from_db()
        self.assertEqual(self.atleta.nome, "Ada")


class AutenticazioneTests(TestCase):
    def _registrazione(self, **override):
        data = {
            "account-email": "mario@example.com",
            "account-password1": "Sup3rSegreta!xyz",
            "account-password2": "Sup3rSegreta!xyz",
            "societa-nome": "ASD Test",
            "societa-codice_fiscale": "ABC123",
        }
        data.update(override)
        return data

    def test_pages_require_login(self):
        for url in ["/atleti/", "/societa/", "/attrezzi/", "/atleti/multiplo/"]:
            r = self.client.get(url)
            self.assertRedirects(r, f"/accedi/?next={url}")

    def test_auth_pages_load(self):
        self.assertEqual(self.client.get("/accedi/").status_code, 200)
        self.assertEqual(self.client.get("/registrazione/").status_code, 200)

    def test_registration_creates_user_societa_and_profile(self):
        r = self.client.post("/registrazione/", self._registrazione())
        self.assertRedirects(r, "/societa/")
        user = get_user_model().objects.get(username="mario@example.com")
        self.assertEqual(user.profilo.societa.nome, "ASD Test")
        self.assertEqual(Profilo.objects.count(), 1)
        self.assertEqual(self.client.get("/atleti/").status_code, 200)  # logged in

    def test_email_is_username_and_societa_email(self):
        self.client.post("/registrazione/", self._registrazione(**{"account-email": "Mario@Example.com"}))
        user = get_user_model().objects.get()
        self.assertEqual(user.username, "mario@example.com")
        self.assertEqual(user.email, user.username)
        self.assertEqual(user.profilo.societa.email, "mario@example.com")

    def test_duplicate_email_rejected(self):
        self.client.post("/registrazione/", self._registrazione())
        self.client.post("/esci/")
        r = self.client.post("/registrazione/", self._registrazione(**{"societa-codice_fiscale": "ZZZ"}))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_login_with_email_is_case_insensitive(self):
        self.client.post("/registrazione/", self._registrazione())
        self.client.post("/esci/")
        r = self.client.post("/accedi/", {"username": "MARIO@example.com", "password": "Sup3rSegreta!xyz"})
        self.assertRedirects(r, "/societa/")

    def test_invalid_societa_creates_nothing(self):
        r = self.client.post("/registrazione/", self._registrazione(**{"societa-nome": ""}))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertEqual(Profilo.objects.count(), 0)

    def test_duplicate_codice_fiscale_creates_nothing(self):
        self.client.post("/registrazione/", self._registrazione())
        self.client.post("/esci/")
        r = self.client.post("/registrazione/", self._registrazione(**{"account-email": "luigi@example.com"}))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_login_and_logout(self):
        get_user_model().objects.create_user("anna", password="Sup3rSegreta!xyz")
        r = self.client.post("/accedi/", {"username": "anna", "password": "Sup3rSegreta!xyz"})
        self.assertRedirects(r, "/societa/")
        self.client.post("/esci/")
        self.assertEqual(self.client.get("/atleti/").status_code, 302)


class IsolamentoSocietaTests(TestCase):
    def setUp(self):
        self.mia = login_con_societa(self.client, "mio", "Mia")
        self.altra = Societa.objects.create(nome="Altra", codice_fiscale="CF-altra", email="a@example.com")
        self.mio_atleta = Atleta.objects.create(nome="Mio", cognome="Atleta", societa=self.mia)
        self.altro_atleta = Atleta.objects.create(nome="Altro", cognome="Atleta", societa=self.altra)

    def test_list_shows_only_own_athletes(self):
        r = self.client.get("/atleti/")
        self.assertEqual(list(r.context["atleti_list"]), [self.mio_atleta])

    def test_societa_list_shows_only_own(self):
        r = self.client.get("/societa/")
        self.assertEqual([x["societa"] for x in r.context["riepiloghi"]], [self.mia])

    def test_root_redirects_to_login_when_anonymous(self):
        self.client.logout()
        self.assertRedirects(self.client.get("/"), "/accedi/")

    def test_root_redirects_to_summary_when_logged_in(self):
        self.assertRedirects(self.client.get("/"), "/societa/")

    def test_other_societa_athlete_is_404(self):
        self.assertEqual(self.client.get(f"/atleti/{self.altro_atleta.pk}/").status_code, 404)
        r = self.client.post(f"/atleti/{self.altro_atleta.pk}/", {"azione": "atleta", "nome": "X", "cognome": "Y"})
        self.assertEqual(r.status_code, 404)
        self.altro_atleta.refresh_from_db()
        self.assertEqual(self.altro_atleta.nome, "Altro")

    def test_new_athlete_is_forced_into_own_societa(self):
        self.client.post("/atleti/nuovo/", {"nome": "Nuova", "cognome": "Atleta", "societa": self.altra.pk})
        self.assertEqual(Atleta.objects.get(nome="Nuova").societa, self.mia)

    def test_edit_cannot_move_athlete_to_other_societa(self):
        self.client.post(f"/atleti/{self.mio_atleta.pk}/",
                         {"azione": "atleta", "nome": "Mio", "cognome": "Atleta", "societa": self.altra.pk})
        self.mio_atleta.refresh_from_db()
        self.assertEqual(self.mio_atleta.societa, self.mia)

    def test_bulk_insert_uses_own_societa(self):
        data = {"atleti-TOTAL_FORMS": 1, "atleti-INITIAL_FORMS": 0, "atleti-MIN_NUM_FORMS": 0,
                "atleti-MAX_NUM_FORMS": 1000, "atleti-0-nome": "B", "atleti-0-cognome": "C",
                "atleti-0-societa": self.altra.pk}
        self.client.post("/atleti/multiplo/", data)
        self.assertEqual(Atleta.objects.get(nome="B").societa, self.mia)

    def test_create_societa_forbidden_for_regular_user(self):
        self.assertEqual(self.client.get("/societa/nuova/").status_code, 403)

    def test_user_without_profile_sees_nothing(self):
        self.client.force_login(get_user_model().objects.create_user("orfano", password="x"))
        r = self.client.get("/atleti/")
        self.assertEqual(list(r.context["atleti_list"]), [])

    def test_superuser_sees_everything(self):
        self.client.force_login(get_user_model().objects.create_superuser("admin", "a@example.com", "x"))
        self.assertEqual(self.client.get("/atleti/").context["atleti_list"].count(), 2)
        self.assertEqual(self.client.get("/societa/nuova/").status_code, 200)


class SquadreTests(TestCase):
    url = "/squadre/nuova/"

    def setUp(self):
        self.mia = login_con_societa(self.client, "mio", "Mia")
        self.altra = Societa.objects.create(nome="Altra", codice_fiscale="CF-altra", email="a@example.com")
        self.mio_atleta = Atleta.objects.create(nome="Mio", cognome="Atleta", societa=self.mia)
        self.altro_atleta = Atleta.objects.create(nome="Altro", cognome="Atleta", societa=self.altra)

    def _data(self, atleti=(), nuovi=(), nome="Under 14"):
        data = {"nome": nome, "anno": "2012", "atleti": [str(a.pk) for a in atleti],
                "nuovi-TOTAL_FORMS": len(nuovi), "nuovi-INITIAL_FORMS": 0,
                "nuovi-MIN_NUM_FORMS": 0, "nuovi-MAX_NUM_FORMS": 1000}
        for i, (n, c) in enumerate(nuovi):
            data[f"nuovi-{i}-nome"] = n
            data[f"nuovi-{i}-cognome"] = c
        return data

    def test_list_shows_only_own_squadre(self):
        mia = Squadra.objects.create(nome="Mia", societa=self.mia)
        Squadra.objects.create(nome="Altrui", societa=self.altra)
        r = self.client.get("/squadre/")
        self.assertEqual(list(r.context["squadre_list"]), [mia])

    def test_page_lists_only_own_athletes(self):
        r = self.client.get(self.url)
        self.assertEqual(list(r.context["atleti_disponibili"]), [self.mio_atleta])

    def test_existing_and_new_athletes_saved_to_own_societa(self):
        r = self.client.post(self.url, self._data(atleti=[self.mio_atleta], nuovi=[("Nuova", "Atleta")]))
        self.assertRedirects(r, "/squadre/")
        squadra = Squadra.objects.get(nome="Under 14")
        self.assertEqual(squadra.societa, self.mia)
        self.assertEqual(set(squadra.atleti.values_list("nome", flat=True)), {"Mio", "Nuova"})
        self.assertEqual(Atleta.objects.get(nome="Nuova").societa, self.mia)

    def test_other_societa_athlete_rejected(self):
        r = self.client.post(self.url, self._data(atleti=[self.altro_atleta], nuovi=[("X", "Y")]))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Squadra.objects.count(), 0)
        self.assertFalse(Atleta.objects.filter(nome="X").exists())

    def test_needs_at_least_one_athlete(self):
        r = self.client.post(self.url, self._data())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Squadra.objects.count(), 0)

    def test_partial_new_athlete_rejected(self):
        r = self.client.post(self.url, self._data(nuovi=[("Solo nome", "")]))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Squadra.objects.count(), 0)


class EsercizioSquadraTests(TestCase):
    def setUp(self):
        self.mia = login_con_societa(self.client, "mio", "Mia")
        self.altra = Societa.objects.create(nome="Altra", codice_fiscale="CF-altra", email="a@example.com")
        self.squadra = Squadra.objects.create(nome="Under 14", societa=self.mia)
        self.altra_squadra = Squadra.objects.create(nome="Altrui", societa=self.altra)
        self.fune = Attrezzo.objects.create(nome="Fune", tipo=Attrezzo.TIPO_SQUADRA)
        self.palla = Attrezzo.objects.create(nome="Palla", tipo=Attrezzo.TIPO_SQUADRA)
        self.url = reverse("dettaglio_squadra", args=[self.squadra.pk])

    def _data(self, rows):
        data = {"esercizi-TOTAL_FORMS": len(rows), "esercizi-INITIAL_FORMS": 0,
                "esercizi-MIN_NUM_FORMS": 0, "esercizi-MAX_NUM_FORMS": 1000}
        for i, (attrezzo, audio) in enumerate(rows):
            data[f"esercizi-{i}-attrezzo"] = attrezzo.pk if attrezzo else ""
            if audio:
                data[f"esercizi-{i}-audio"] = audio
        return data

    def test_saves_squad_exercises_with_audio(self):
        with override_settings(MEDIA_ROOT=_MEDIA):
            r = self.client.post(self.url, self._data([
                (self.fune, SimpleUploadedFile("fune.mp3", b"abc", "audio/mpeg")),
                (self.palla, SimpleUploadedFile("palla.wav", b"def", "audio/wav")),
            ]))
        self.assertRedirects(r, self.url)
        self.assertEqual(EsercizioSquadra.objects.filter(squadra=self.squadra).count(), 2)
        e = EsercizioSquadra.objects.get(attrezzo=self.fune)
        self.assertEqual(e.nome_file_audio, "fune.mp3")
        self.assertIn(f"esercizi/squadre/{self.squadra.pk}/", e.audio.name)

    def test_audio_required_for_chosen_attrezzo(self):
        r = self.client.post(self.url, self._data([(self.fune, None)]))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(EsercizioSquadra.objects.count(), 0)

    def test_duplicate_attrezzo_rejected(self):
        with override_settings(MEDIA_ROOT=_MEDIA):
            r = self.client.post(self.url, self._data([
                (self.fune, SimpleUploadedFile("a.mp3", b"abc")),
                (self.fune, SimpleUploadedFile("b.mp3", b"abc")),
            ]))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(EsercizioSquadra.objects.count(), 0)

    def test_at_least_one_required(self):
        r = self.client.post(self.url, self._data([(None, None)]))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(EsercizioSquadra.objects.count(), 0)

    def test_other_societa_squadra_is_404(self):
        url = reverse("dettaglio_squadra", args=[self.altra_squadra.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, self._data([(self.fune, None)])).status_code, 404)


class TipoAttrezzoTests(TestCase):
    def setUp(self):
        self.mia = login_con_societa(self.client, "mio", "Mia")
        self.atleta = Atleta.objects.create(nome="A", cognome="B", societa=self.mia)
        self.squadra = Squadra.objects.create(nome="S", societa=self.mia)
        self.fune = Attrezzo.objects.create(nome="Fune")  # default: atleta
        self.nastro = Attrezzo.objects.create(nome="Nastro", tipo=Attrezzo.TIPO_SQUADRA)

    def test_default_is_atleta(self):
        self.assertEqual(self.fune.tipo, Attrezzo.TIPO_ATLETA)

    def test_athlete_page_offers_only_atleta_attrezzi(self):
        r = self.client.get(f"/atleti/{self.atleta.pk}/")
        choices = list(r.context["formset"].empty_form.fields["attrezzo"].queryset)
        self.assertEqual(choices, [self.fune])

    def test_squadra_page_offers_only_squadra_attrezzi(self):
        r = self.client.get(f"/squadre/{self.squadra.pk}/")
        choices = list(r.context["formset"].empty_form.fields["attrezzo"].queryset)
        self.assertEqual(choices, [self.nastro])

    def test_athlete_cannot_use_squadra_attrezzo(self):
        data = {"azione": "esercizi", "esercizi-TOTAL_FORMS": 1, "esercizi-INITIAL_FORMS": 0,
                "esercizi-MIN_NUM_FORMS": 0, "esercizi-MAX_NUM_FORMS": 1000,
                "esercizi-0-attrezzo": self.nastro.pk,
                "esercizi-0-audio": SimpleUploadedFile("n.mp3", b"abc")}
        r = self.client.post(f"/atleti/{self.atleta.pk}/", data)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Esercizio.objects.count(), 0)


class AttrezzoAttivoTests(TestCase):
    def test_inactive_attrezzo_not_offered(self):
        from .forms import EsercizioForm
        attivo = Attrezzo.objects.create(nome="Fune")
        Attrezzo.objects.create(nome="Palla", is_active=False)
        self.assertTrue(Attrezzo.objects.get(pk=attivo.pk).is_active)
        self.assertEqual(list(EsercizioForm().fields["attrezzo"].queryset), [attivo])
