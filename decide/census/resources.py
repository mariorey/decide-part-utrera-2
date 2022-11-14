from import_export import resources
from .models import Census

class CensusResources(resources.ModelResource):
	class Meta:
		model = Census