from django.urls import path, include
from . import views
from census.views import *

urlpatterns = [
    path('', views.CensusCreate.as_view(), name='census_create'),
    path('<int:voting_id>/', views.CensusDetail.as_view(), name='census_detail'),
    path('export/<format>/',views.export),
    path('exportbyVoting/<int:voting_id>/<format>/',views.exportByVoting),
    path('exportbyVoter/<int:voter_id>/<format>/',views.exportByVoter)
]
