from django.db import models


class Attrezzo(models.Model):

    class Meta:
        verbose_name = "Attrezzo"
        verbose_name_plural = "Attrezzi"

    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome
    

class Categoria(models.Model):

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorie"

    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


class Fascia(models.Model):

    class Meta:
        verbose_name = "Fascia"
        verbose_name_plural = "Fasce"

    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


class Livello(models.Model):

    class Meta:
        verbose_name = "Livello"
        verbose_name_plural = "Livelli"

    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


class Societa(models.Model):

    class Meta:
        verbose_name = "Società"
        verbose_name_plural = "Società"

    nome = models.CharField(max_length=100)
    codice_fiscale = models.CharField(max_length=100, unique=True)

    indirizzo = models.CharField(max_length=200, blank=True, null=True)
    numero_civico = models.CharField(max_length=10, blank=True, null=True)
    citta = models.CharField(max_length=100, blank=True, null=True)
    cap = models.CharField(max_length=10, blank=True, null=True)

    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField()

    partita_iva = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.nome
    

class Atleta(models.Model):

    class Meta:
        verbose_name = "Atleta"
        verbose_name_plural = "Atleti"

    nome = models.CharField(max_length=100)
    cognome = models.CharField(max_length=100)

    anno_nascita = models.IntegerField(blank=True, null=True)

    email = models.EmailField(blank=True, null=True)

    societa = models.ForeignKey(Societa, on_delete=models.SET_NULL, blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, blank=True, null=True)
    fascia = models.ForeignKey(Fascia, on_delete=models.SET_NULL, blank=True, null=True)
    livello = models.ForeignKey(Livello, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f"{self.nome} {self.cognome}"
    

class Competizione(models.Model):

    class Meta:
        verbose_name = "Competizione"
        verbose_name_plural = "Competizioni"

    nome = models.CharField(max_length=100)
    data_inizio = models.DateField(blank=True, null=True)
    data_fine = models.DateField(blank=True, null=True)
    descrizione = models.TextField(blank=True, null=True)

    indirizzo = models.CharField(max_length=200, blank=True, null=True)
    numero_civico = models.CharField(max_length=10, blank=True, null=True)
    citta = models.CharField(max_length=100, blank=True, null=True)
    cap = models.CharField(max_length=10, blank=True, null=True)

    data_inizio_iscrizioni = models.DateField(blank=True, null=True)
    data_fine_iscrizioni = models.DateField(blank=True, null=True)
    
    data_termine_pagamento = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.nome