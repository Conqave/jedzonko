from django.db import models


class PromotionAccess(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = [("view_promotions", "Can view promotions")]
