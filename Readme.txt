
Steps to Run the program

Firstly data those three csv file in data directory under report
  - name csvfile containing store status as data1.csv
  - name csvfile containing store opening and closing time as data2.csv
  - name csvfile containing store timezone as data3.csv


1- create a Virtual Environment

2- pip install requirements.txt

3- python manage.py makemigrations

4- python manage.py migrate

#this command will pre fill database from csv files if database if allready filled don't run this command
5- python manage.py FillDatabase

6- python manage.py runserver

# this command will start celery worker
7- celery -A loop worker --loglevel=info 

8- goto http://127.0.0.1:8000/trigger_report/


#this command will download csv if report is genrated otherwise will return json response
9- goto http://127.0.0.1:8000/get_report/<reportid>/


Logic-
we used is if we get a store active on any poll then we consider it to be active before and after 30 mins
of poll time unless that time goes out of business hours

If we didn't got of particular hour we didn't count that hour as active or inactive
