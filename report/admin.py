from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(Store)
admin.site.register(StoreStatus)
admin.site.register(StoreTime)
admin.site.register(Report)
admin.site.register(Latest)