from django.test import TestCase

# Create your tests here.


import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Atleta, Attrezzo, Esercizio

_MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=_MEDIA)
class DettaglioAtletaTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(_MEDIA, ignore_errors=True)

    def setUp(self):
        self.atleta = Atleta.objects.create(nome="Ada", cognome="Rossi")
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
        self.atleta = Atleta.objects.create(nome="Ada", cognome="Rossi")
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
