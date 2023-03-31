from django.db import models

import pytz
TIMEZONES = tuple(zip(pytz.all_timezones, pytz.all_timezones))
STATUS_CHOICES = (
    ('active', 'active'),
    ('inactive', 'inactive'),
)

class Store(models.Model):
    storeid=models.CharField(max_length=50,primary_key=True)
    timezone = models.CharField(max_length=32, choices=TIMEZONES, default='America/Chicago')
    def __str__(self):
        return f'{self.storeid}-{self.timezone}'
class StoreStatus(models.Model):
    storeid=models.ForeignKey(Store,on_delete=models.CASCADE)
    timestamp=models.DateTimeField()
    status=models.CharField(choices=STATUS_CHOICES,max_length=10)
    class Meta:
        unique_together = ('timestamp', 'storeid')
    def __str__(self):
        return f'{self.storeid_id}-{self.timestamp}-{self.status}'

class StoreTime(models.Model):
    storeid=models.ForeignKey(Store,on_delete=models.CASCADE)
    day=models.IntegerField()
    store_start_time=models.TimeField()
    store_end_time=models.TimeField()
    class Meta:
        unique_together = ('day', 'storeid','store_start_time')
    def __str__(self):
        return f'{self.storeid_id}-{self.day}-{str(self.store_start_time)}'
    



def content_file_name(instance, filename):
    # name, ext = filename.split('.')
    file_path = 'csv-report/{filename}.csv'.format(
        filename=instance.reportId,)
    return file_path
class Report(models.Model):
    reportId=models.CharField(max_length=12,primary_key=True)
    task_id=models.CharField(max_length=50,null=True,blank=True)
    status=models.CharField(max_length=15,default='Running')
    report=models.FileField(upload_to=content_file_name, null=True, blank=True)

class Latest(models.Model):
    timestamp=models.DateTimeField()

