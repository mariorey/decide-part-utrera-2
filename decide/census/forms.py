from django import forms
from django.contrib.auth.models import User

class CensusCreateForm(forms.Form):
    voters = forms.ModelChoiceField(label='Votante que se va a añadir', queryset=User.objects.all(), required=True)