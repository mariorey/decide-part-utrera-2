from django.db import models


class Census(models.Model):
    voting_id = models.PositiveIntegerField()
    voter_id = models.PositiveIntegerField()

    def get_all_objects(self):
        queryset = self._meta.model.objects.all()
        # can use the below method also
        # queryset = self.__class__.objects.all()   
        return queryset

    class Meta:
        unique_together = (('voting_id', 'voter_id'),)
