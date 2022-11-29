from django.urls import path, include
from . import views
from census.views import *

urlpatterns = [
    path('', views.CensusCreate.as_view(), name='census_create'),
    path('<int:voting_id>/', views.CensusDetail.as_view(), name='census_detail'),
    path('reuse/<int:old_voting>/<int:new_voting>/',views.reuseCensus),
    path('showAll/', views.censusShow, name='ShowAllCensus'),
    path('detail/<int:id>/',views.censusShowDetails,name ="showDetails"),
    path('voting/<int:voting_id>', views.votersInVoting, name = "votersInVoting"),
    path('voting/', views.showVotings, name="showVotings"),
    path('voting/<int:voting_id>/create', views.createCensus, name = "createCensus"),
    path('voting/<int:voting_id>/<int:voter_id>/delete', views.deleteVoter, name="deleteVoter"),
    path('<int:voting_id>/<int:voter_id>/delete', views.deleteCensus, name="deleteCensus"),
    path('addLDAPcensusVotacion/', importCensusFromLdapVotacion, name='addLDAPcensusVotacion'),
    path('importExcel/', importar, name='importExcel'),
    path('export/<format>/',views.export),
    path('exportbyVoting/<int:voting_id>/<format>/',views.exportByVoting, name='exportByVoting'),
    path('exportbyVoter/<int:voter_id>/<format>/',views.exportByVoter),
    path('exportAllCensus/',views.exportAllCensus, name = 'exportAllCensus'),
    path('exportCensusByVoter/',views.exportCensusByVoter, name = 'exportCensusByVoter'),
    path('exportCensusByVoting/',views.exportCensusByVoting, name = 'exportCensusByVoting'),
    path('reuseview/',views.reuseview),
    path('reuse/',views.reuseview, name="reuseview")    
]
