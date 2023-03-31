from celery import shared_task
import random
from .models import *
from datetime import datetime,timedelta
import pytz
import math
from django.db.models import Q
import csv
from io import BytesIO
from django.http import HttpResponse
from django.core.files.base import ContentFile
from celery.result import AsyncResult
import os
from loop.settings import BASE_DIR



def get_activity_last_hour(local_datetime_obj,store_start_time,store_end_time,timezone,dt_obj1,local_curr_datetime_obj,start_time_of_last_hour):
    store_opening_dateTime=datetime.combine(local_datetime_obj,store_start_time,tzinfo=timezone)
    store_closing_dateTime=datetime.combine(local_datetime_obj,store_end_time,tzinfo=timezone)
    end_time_for_this_hour=dt_obj1.astimezone(timezone)+ timedelta(minutes=30)
    overlap_end_time=min(end_time_for_this_hour,local_curr_datetime_obj, store_closing_dateTime)
                               
    start_time_for_this_hour=dt_obj1.astimezone(timezone)- timedelta(minutes=30)
    overlap_start_time = max(start_time_for_this_hour,start_time_of_last_hour, store_opening_dateTime)
                           
    overlap_time = overlap_end_time - overlap_start_time
    activity_last_hour=(overlap_time.total_seconds()/60)
    return activity_last_hour

def get_activity_this_hour(local_datetime_obj,store_start_time,store_end_time,timezone,dt_obj1,local_curr_datetime_obj,start_time_of_last_day_or_week):
    store_opening_dateTime=datetime.combine(local_datetime_obj,store_start_time,tzinfo=timezone)
    store_closing_dateTime=datetime.combine(local_datetime_obj,store_end_time,tzinfo=timezone)
    end_time_for_this_hour=dt_obj1.astimezone(timezone)+ timedelta(minutes=30)
    overlap_end_time=min(end_time_for_this_hour,local_curr_datetime_obj, store_closing_dateTime)
    start_time_for_this_hour=dt_obj1.astimezone(timezone)- timedelta(minutes=30)
    overlap_start_time = max(start_time_of_last_day_or_week,start_time_for_this_hour, store_opening_dateTime)
    overlap_time = overlap_end_time - overlap_start_time
    activity_this_hour=(overlap_time.total_seconds()/3600)
    return activity_this_hour


def get_updated_data():
    storeStatusList=[]
    currTimeStamp=Latest.objects.latest('timestamp').timestamp
    latest_timeStamp=currTimeStamp
    with open(os.path.join(BASE_DIR, 'report/data/data1.csv'),'r') as file:
        reader=csv.reader(file)
        next(reader)
        timestamp_format1 = '%Y-%m-%d %H:%M:%S.%f %Z'
        timestamp_format2 = '%Y-%m-%d %H:%M:%S %Z'
        for row in reader:
            if '.' in row[2]:
                timestamp_format = timestamp_format1
            else:
                timestamp_format = timestamp_format2
                timestamp = datetime.strptime(row[2], timestamp_format)
                timestamp_utc = pytz.utc.localize(timestamp)
                if timestamp_utc>currTimeStamp:
                    latest_timeStamp=max(latest_timeStamp,timestamp_utc)
                    storeStatusList.append(
                    StoreStatus(
                        storeid_id=row[0],
                        timestamp=timestamp_utc,
                        status=row[1],
                        )
                    )
        if len(storeStatusList)>0:
            StoreStatus.objects.bulk_create(storeStatusList)
            Latest.objects.create(timestamp=latest_timeStamp)




@shared_task
def generate_report(report_id):
    get_updated_data()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="mydata.csv"'
    currTimeStamp=Latest.objects.latest('timestamp').timestamp
    dt_obj = datetime.fromisoformat(str(currTimeStamp))
    one_week_ago = (dt_obj - timedelta(days=7))
    writer=csv.writer(response)
    writer.writerow(['store_id','uptime_last_hour','uptime_last_day','uptime_last_week','downtime_last_hour','downtime_last_day','downtime_last_week'])
    cnt=0
    allStores = Store.objects.prefetch_related('storestatus_set').all()
    for x in allStores:
        cnt+=1
        # print(uptime_last_hour(x.storeid))
        uptime_last_hour=0
        uptime_last_day=0
        uptime_last_week=0
        downtime_last_hour=0
        downtime_last_day=0
        downtime_last_week=0
        active_min=0
        inactive_min=0
        # obj=StoreStatus.objects.filter(storeid=x).order_by('-timestamp')
        obj=x.storestatus_set.all()
        n=len(obj)
        timezone = pytz.timezone(x.timezone)
        local_curr_datetime_obj=dt_obj.astimezone(timezone)
        start_time_of_last_hour=dt_obj.astimezone(timezone)- timedelta(hours=1)
        start_time_of_last_day=dt_obj.astimezone(timezone)- timedelta(days=1)
        start_time_of_last_week=dt_obj.astimezone(timezone)- timedelta(days=7)
        prev=None
        i=0
        for y in obj:
            dt_obj1 = datetime.fromisoformat(str(y.timestamp))
            local_datetime_obj = dt_obj1.astimezone(timezone)
            if one_week_ago>dt_obj1:
                break
            next=None
            if i+1<n:
                next=obj[i+1]
            if next is not None:
                dt_obj2 = datetime.fromisoformat(str(next.timestamp))
                local_datetime_obj2 = dt_obj2.astimezone(timezone)
            
            timeObj=StoreTime.objects.filter(day=local_datetime_obj.weekday(),storeid=x)
            if len(timeObj)==0:
                if start_time_of_last_hour<local_datetime_obj:
                    if y.status=='active':
                        uptime_last_hour=60
                    else:
                        downtime_last_hour=60
                elif start_time_of_last_day<local_datetime_obj:
                    if y.status=='active':
                        uptime_last_day+=1
                    else:
                        downtime_last_day+=1
                else:
                    if y.status=='active':
                        uptime_last_week+=1
                    else:
                        downtime_last_week+=1

            for z in timeObj:
                
                store_opening_dateTime=datetime.combine(local_datetime_obj,z.store_start_time,tzinfo=timezone)
                store_closing_dateTime=datetime.combine(local_datetime_obj,z.store_end_time,tzinfo=timezone)
                
                if z.store_start_time<=local_datetime_obj.time() and z.store_end_time>=local_datetime_obj.time():
                    if start_time_of_last_hour<local_datetime_obj:
                        if y.status=='active':
                            uptime_last_hour+=get_activity_last_hour(local_datetime_obj,z.store_start_time,z.store_end_time,timezone,dt_obj1,local_curr_datetime_obj,start_time_of_last_hour)
                            uptime_last_hour=min(uptime_last_hour,60)

                        else:
                            
                            downtime_last_hour+=get_activity_last_hour(local_datetime_obj,z.store_start_time,z.store_end_time,timezone,dt_obj1,local_curr_datetime_obj,start_time_of_last_hour)
                            downtime_last_hour=min(downtime_last_hour,60)
                    elif start_time_of_last_day<local_datetime_obj:
                        if y.status=='active':
                            
                            uptime_last_day+=get_activity_this_hour(local_datetime_obj,z.store_start_time,z.store_end_time,timezone,dt_obj1,local_curr_datetime_obj,start_time_of_last_day)
                            uptime_last_day=min(uptime_last_day,24)
                            
                        else:
                            downtime_last_day+=get_activity_this_hour(local_datetime_obj,z.store_start_time,z.store_end_time,timezone,dt_obj1,local_curr_datetime_obj,start_time_of_last_day)
                            downtime_last_day=min(downtime_last_day,24)
                    else:
                        if y.status=='active':
                           
                            # uptime_last_day+=(overlap_time.total_seconds()/3600)
                            uptime_last_week+=get_activity_this_hour(local_datetime_obj,z.store_start_time,z.store_end_time,timezone,dt_obj1,local_curr_datetime_obj,start_time_of_last_week)
                            
                        else:
                            
                            downtime_last_week+=get_activity_this_hour(local_datetime_obj,z.store_start_time,z.store_end_time,timezone,dt_obj1,local_curr_datetime_obj,start_time_of_last_week)
        uptime_last_hour=math.floor(uptime_last_hour)
        uptime_last_day=math.floor(uptime_last_day+(uptime_last_hour)/60)
        uptime_last_week=math.floor(uptime_last_week+uptime_last_day)
        downtime_last_hour=math.floor(downtime_last_hour)
        downtime_last_day=math.floor(downtime_last_day+(downtime_last_hour)/60)
        downtime_last_week=math.floor(downtime_last_week+(downtime_last_day))
        writer.writerow([x.storeid,uptime_last_hour,uptime_last_day,uptime_last_week,downtime_last_hour,downtime_last_day,downtime_last_week])
    report=Report.objects.get(reportId=report_id)
    csv_data = BytesIO()
    csv_data.write(response.content)
    # report.report= ContentFile(csv_data.getvalue())
    report.report.save('report.csv', ContentFile(csv_data.getvalue()))
    # report.save()
    report.status="Completed"
    report.save()
    # set_task_status(report_id)           
    return ('done')

