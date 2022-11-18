from django.urls import path, include
from . import views


urlpatterns = [
    path('', views.CensusCreate.as_view(), name='census_create'),
    path('<int:voting_id>/', views.CensusDetail.as_view(), name='census_detail'),
    path('showAll/', views.censusShow, name='ShowAllCensus'),
    path('detail/<int:id>/',views.censusShowDetails,name ="showDetails"),
    path('voting/<int:voting_id>', views.votersInVoting, name = "votersInVoting")

]
