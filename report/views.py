from django.shortcuts import render
import csv
from .models import *
from rest_framework.decorators import api_view
from rest_framework.response import Response
from report.tasks import generate_report
import string
import random
from celery.result import AsyncResult
from django.http import FileResponse
# from celery.result import AsyncResult
# import time
import json
from django.http import FileResponse, StreamingHttpResponse

@api_view(['GET'])
def trigger_report(request,*args, **kwargs):
    report_id = ''.join(random.choices(string.ascii_lowercase +string.digits, k=10))
    while (Report.objects.filter(pk=report_id).exists()):
        report_id = ''.join(random.choices(string.ascii_lowercase +string.digits, k=10))
    result = generate_report.delay(report_id)
    Report.objects.create(
        reportId=report_id,
        task_id=result.task_id
    )
    # set_task_status.delay(report_id)
    return Response({'report_id':report_id})


@api_view(['GET','POST'])
def get_report(request,pk,*args, **kwargs):
    try:
        instance=Report.objects.get(reportId=pk)
        
        if instance.status=='Running':
            return Response({'status': 'Running'})
        else:
            csv_file = instance.report
            response = FileResponse(csv_file, as_attachment=True,)
            return Response({"status":"completed",'file':response})
            # return response
    except Exception as e:
        print("dkdfjkdfffkf")
        return Response({'status':'error','message':e})
    


@api_view(['GET'])
def get_report(request,pk,*args, **kwargs):
    try:
        instance=Report.objects.get(reportId=pk)
        
        if instance.status=='Running':
            return Response({'status': 'Running'})
        else:
            csv_file = instance.report
            response = FileResponse(csv_file, as_attachment=True,)
            return response
            # return response
    except Exception as e:
        print("dkdfjkdfffkf")
        return Response({'status':'error','message':e})
    
    