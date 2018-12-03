import requests,sqlite3,time,datetime,json, objectpath, traceback, atexit
from apscheduler.schedulers.background import BackgroundScheduler
from threading import Thread
from datetime import datetime,timedelta
from API_REC_TRANS import *
import time

'''Datenbank fuer Taxifahrer'''
DatabaseFile = 'drivers.sqlite3'

'''BackgroundTask'''
def backGroundT():
    con = sqlite3.connect(DatabaseFile)
    curs = con.cursor()
    curs.execute("SELECT staff_number, Status FROM driver")
    rows = curs.fetchall()
    x = 0
    for row in rows:
        Lampensteuerung(rows[x][0], rows[x][1])
        x = x + 1
    con.commit()
    con.close()
    beendeFahrt(

    )

while(True):
    backGroundT()
    time.sleep(4.5)