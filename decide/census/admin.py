from django.contrib import admin
from .models import Census
from django.http import HttpResponse
from import_export import resources
from import_export.admin import ImportExportModelAdmin

class CensusResource(resources.ModelResource):
    class Meta:
        model = Census

class CensusAdmin(ImportExportModelAdmin,admin.ModelAdmin):
    list_display = ('voting_id', 'voter_id')
    list_filter = ('voting_id', )
    resource_class = CensusResource

    search_fields = ('voter_id', )


admin.site.register(Census, CensusAdmin)
