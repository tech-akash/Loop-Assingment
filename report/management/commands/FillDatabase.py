from django.core.management.base import BaseCommand
from ...models import *
import csv
import os
from loop.settings import BASE_DIR
from datetime import datetime
class Command(BaseCommand):
    help = 'My custom command'

    def handle(self, *args, **options):
        storeList=[]
        storeTimeList=[]
        storeStatusList=[]
        unique_store = set()
        file_path = os.path.join(BASE_DIR, '/report/data/data3.csv')
        print(file_path)
        with open(os.path.join(BASE_DIR, 'report/data/data3.csv'), 'r') as file:
            reader=csv.reader(file)
            next(reader)
            for row in reader:
                if row[0] not in unique_store:
                    unique_store.add(row[0])
                    storeList.append(
                        Store(
                            storeid=row[0],
                            timezone=row[1]
                        )
                    )
        with open(os.path.join(BASE_DIR, 'report/data/data2.csv'),'r') as file:
            reader=csv.reader(file)
            next(reader)
            for row in reader:
                storeTimeList.append(
                    StoreTime(
                        storeid_id=row[0],
                        day=row[1],
                        store_start_time=row[2],
                        store_end_time=row[3]
                    )
                )
                if row[0] not in unique_store:
                    unique_store.add(row[0])
                    storeList.append(
                        Store(
                            storeid=row[0]
                        )
                    )
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
                storeStatusList.append(
                    StoreStatus(
                        storeid_id=row[0],
                        timestamp=timestamp_utc,
                        status=row[1],
                    )
                )
                if row[0] not in unique_store:
                    unique_store.add(row[0])
                    storeList.append(
                        Store(
                            storeid=row[0]
                        )
                    )
        Store.objects.bulk_create(storeList)
        StoreTime.objects.bulk_create(storeTimeList)
        StoreStatus.objects.bulk_create(storeStatusList)