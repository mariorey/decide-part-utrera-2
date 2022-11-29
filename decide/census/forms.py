from django import forms
from django.contrib.auth.models import User
from voting.models import *
from census.models import Census
from django.forms import ModelMultipleChoiceField
from django.contrib.auth.forms import UserCreationForm


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
                                
class UserRegisterForm(UserCreationForm):
    username = forms.CharField(label='Nombre de usuario',widget=forms.TextInput(attrs={'placeholder': 'Nombre de Usuario','class':'form-control'}))
    email = forms.EmailField(label='Dirección de correo electrónico',required=False, widget = forms.EmailInput(attrs={'placeholder': 'Dirección de correo electrónico','class':'form-control'}))
    password1 = forms.CharField(label='Contraseña', widget = forms.PasswordInput(attrs={'placeholder': 'Contraseña','class':'form-control'}))
    password2 = forms.CharField(label='Confirma contraseña', widget = forms.PasswordInput(attrs={'placeholder': 'Confirmar Contraseña','class':'form-control'}))

    class Meta: 
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        help_texts = {k:"" for k in fields}

