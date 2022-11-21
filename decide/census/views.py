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
from voting.models import Voting
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .forms import *
from django.contrib import messages
from django.contrib.auth.decorators import login_required


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
        voters = Census.objects.filter(
            voting_id=voting_id).values_list('voter_id', flat=True)
        return Response({'voters': voters})


class CensusDetail(generics.RetrieveDestroyAPIView):

    def destroy(self, request, voting_id, *args, **kwargs):
        voters = request.data.get('voters')
        census = Census.objects.filter(
            voting_id=voting_id, voter_id__in=voters)
        census.delete()
        return Response('Voters deleted from census', status=ST_204)

    def retrieve(self, request, voting_id, *args, **kwargs):
        voter = request.GET.get('voter_id')
        try:
            Census.objects.get(voting_id=voting_id, voter_id=voter)
        except ObjectDoesNotExist:
            return Response('Invalid voter', status=ST_401)
        return Response('Valid voter')


def censusShow(request):
    context = {
        'allCensus': Census.objects.all(),
    }
    return render(request, "showAllCensus.html", context)


def censusShowDetails(request, id):
    context = {
        'census': Census.objects.get(id=id)
    }
    return render(request, "census_detail.html", context)


def votersInVoting(request, voting_id):
    censusByVoting = Census.objects.filter(voting_id=voting_id)
    voters = []
    for census in censusByVoting:
        voter = User.objects.get(id=census.voter_id)
        voters.append(voter)
    context = {
        'voters': voters,
        'voting_id': voting_id
    }
    return render(request, "votersInVoting.html", context)


def showVotings(request):
    votings = Voting.objects.all()
    context = {
        'votings': votings
    }
    return render(request, "showAllVotings.html", context)


def createCensus(request, voting_id):
    if request.method == 'POST':
        if request.user.is_staff:
            form = CensusCreateForm(request.POST)
            if form.is_valid():
                voter = form.cleaned_data['voters']
                census = Census(voting_id=voting_id, voter_id=voter.id)
                try:
                    census.save()
                except IntegrityError:
                    messages.add_message(
                        request, messages.ERROR, "El usuario no se ha añadido ya que estaba en la base de datos")
        else:
            messages.add_message(
                        request, messages.ERROR, "El usuario no tiene permisos de administrador")
        return redirect('/census/voting/%s' % (voting_id))
    else:
        form = CensusCreateForm()
        context = {
            'voting_id': voting_id,
            'form': form
        }
        return render(request, "createCensus.html", context)

def deleteCensus(request, voting_id, voter_id):
    if request.user.is_staff:
        census = Census.objects.get(voting_id = voting_id, voter_id = voter_id)
        try:
            census.delete()
        except IntegrityError:
            messages.add_message(
                        request, messages.ERROR, "No se ha podido eliminar al votante")
    else:
        messages.add_message(
                        request, messages.ERROR, "El usuario no tiene permisos de administrador")
    return redirect('/census/voting/%s' % (voting_id))