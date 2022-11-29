from django import forms
from django.contrib.auth.models import User
from voting.models import *
from census.models import Census
from django.forms import ModelMultipleChoiceField

FORMAT = [
    ('csv','csv'),
    ('xls','xls'),
    ('json','json'),
    ]

class CensusCreateForm(forms.Form):
    voters = forms.ModelChoiceField(label='Votante que se va a añadir', queryset=User.objects.all(), required=True)

class CensusAddLdapFormVotacion(forms.Form):
    """This form contains the necessary data to perform the LDAP method.

       Atributtes:
            Voting (Votacion)
            urlLdap (String)
            treeSufix (String)
            branch (String)
            pwd (String)
    """
    voting = forms.ModelChoiceField(label='Votación a la que desea añadir censo', empty_label="-",
                                     queryset=Voting.objects.all().filter(end_date__isnull=True), required=True,)

    urlLdap = forms.CharField(label='Url del servidor LDAP',
                                widget=forms.TextInput(attrs={'placeholder': 'ldap.ServerUrl:Port'}),
                                required=True)

    treeSufix = forms.CharField(label='Rama del arbol del administrador LDAP',
                                widget=forms.TextInput(attrs={'placeholder': 'cn=admin,dc=YourDomain,dc=com'}),
                                required=True)

    branch = forms.CharField(label='Rama a buscar del LDAP',
                                widget=forms.TextInput(attrs={'placeholder': 'dc=YourDomain,dc=com'}),
                                required=True)

    pwd = forms.CharField(label='Contraseña del administrador LDAP',
                                widget=forms.TextInput(attrs={'placeholder': 'Password'}), required=True)


class ExportAllCensusForm(forms.Form):
    formato = forms.ChoiceField(choices = FORMAT)

class ExportCensusByVoterForm(forms.Form):
    formato = forms.ChoiceField(choices = FORMAT)
    voter = forms.ModelChoiceField(label='Votante por el que filtrar', queryset=User.objects.all(), required=True)


class ExportCensusByVotingForm(forms.Form):
    formato = forms.ChoiceField(choices = FORMAT)
    voting = forms.ModelChoiceField(label='Votación por la que filtrar', queryset=Voting.objects.all(), required=True)

