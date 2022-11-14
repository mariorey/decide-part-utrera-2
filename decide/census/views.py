from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.status import (
        HTTP_201_CREATED as ST_201,
        HTTP_204_NO_CONTENT as ST_204,
        HTTP_400_BAD_REQUEST as ST_400,
        HTTP_401_UNAUTHORIZED as ST_401,
        HTTP_409_CONFLICT as ST_409
)

from base.perms import UserIsStaff
from .models import Census
from django.contrib import messages
from django.shortcuts import render, redirect
from .ldapFunctions import LdapCensus
from census.forms import *
from voting.models import Voting
from django.contrib.auth.models import User


class CensusCreate(generics.ListCreateAPIView):
    permission_classes = (UserIsStaff,)

    def create(self, request, *args, **kwargs):
        voting_id = request.data.get('voting_id')
        voters = request.data.get('voters')
        try:
            for voter in voters:
                census = Census(voting_id=voting_id, voter_id=voter)
                census.save()
        except IntegrityError:
            return Response('Error try to create census', status=ST_409)
        return Response('Census created', status=ST_201)

    def list(self, request, *args, **kwargs):
        voting_id = request.GET.get('voting_id')
        voters = Census.objects.filter(voting_id=voting_id).values_list('voter_id', flat=True)
        return Response({'voters': voters})


class CensusDetail(generics.RetrieveDestroyAPIView):

    def destroy(self, request, voting_id, *args, **kwargs):
        voters = request.data.get('voters')
        census = Census.objects.filter(voting_id=voting_id, voter_id__in=voters)
        census.delete()
        return Response('Voters deleted from census', status=ST_204)

    def retrieve(self, request, voting_id, *args, **kwargs):
        voter = request.GET.get('voter_id')
        try:
            Census.objects.get(voting_id=voting_id, voter_id=voter)
        except ObjectDoesNotExist:
            return Response('Invalid voter', status=ST_401)
        return Response('Valid voter')

def importCensusFromLdapVotacion(request):
    """This method processes the parameters sent by the form to call the connection method and the import LDAP method
    to be able to create the census containing the users from the LDAP branch previously especified. This will work
    if the users are already registered on the system.  
        
    Args:
        request: contains the HTTP data of the LDAP import
        """ 
    if request.user.is_staff:

        if request.method == 'POST':
            form = CensusAddLdapFormVotacion(request.POST)

            if form.is_valid():
                urlLdap = form.cleaned_data['urlLdap']
                treeSufix = form.cleaned_data['treeSufix']
                pwd = form.cleaned_data['pwd']
                branch = form.cleaned_data['branch']
                voting = form.cleaned_data['voting'].__getattribute__('pk')

                voters = User.objects.all()
                usernameList = LdapCensus().ldapGroups(urlLdap, treeSufix, pwd, branch)

                userList = []
                for username in usernameList:
                    user = voters.filter(username=username)
                    if user:
                        user = user.values('id')[0]['id']
                        userList.append(user)

            if request.user.is_authenticated:
                for username in userList:
                    census = Census(voting_id=voting, voter_id=username)
                    census_list = Census.objects.all()
                    census.save()

            return redirect('/admin/census/census')
        else:
            form = CensusAddLdapFormVotacion()

        context = {
            'form': form,
        }
        return render(request, template_name='importarCensusLdapVotacion.html', context=context)
    else:
        messages.add_message(request, messages.ERROR, "permiso denegado")
        return redirect('/admin')


