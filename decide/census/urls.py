from django.urls import path, include
from . import views
from census.views import *


urlpatterns = [
    path('', views.CensusCreate.as_view(), name='census_create'),
    path('<int:voting_id>/', views.CensusDetail.as_view(), name='census_detail'),
    path('showAll/', views.censusShow, name='ShowAllCensus'),
    path('detail/<int:id>/',views.censusShowDetails,name ="showDetails"),
    path('voting/<int:voting_id>', views.votersInVoting, name = "votersInVoting"),
    path('voting/', views.showVotings, name="showVotings"),
    path('voting/<int:voting_id>/create', views.createCensus, name = "createCensus"),
    path('voting/<int:voting_id>/<int:voter_id>/delete', views.deleteCensus, name="deleteCensus"),
    path('addLDAPcensusVotacion/', importCensusFromLdapVotacion, name='addLDAPcensusVotacion'),
    path('importExcel/', importar, name='importExcel')
]
