from django.db import models



class Census(models.Model):
    voting_id = models.PositiveIntegerField()
    voter_id = models.PositiveIntegerField()

    class Meta:
        unique_together = (('voting_id', 'voter_id'),)

    def get_absolute_url(self):
        return "/census/detail/%s" %(self.id)

