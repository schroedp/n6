import requests,sqlite3,time,datetime,json, objectpath, traceback, atexit
from apscheduler.schedulers.background import BackgroundScheduler
from threading import Thread
from datetime import datetime,timedelta
from dateutil.parser import parse
import asyncio

'''Datenbank fuer Taxifahrer'''
DatabaseFile = 't4.sqlite3'

'''ID und Code für Developer.here '''
mapID = "FCNS06QeItEtJinJGrbA"
mapCode = "Bf4Os0ScXYrDgIkNnvw1DA"

'''Zugriffsdaten fuer die Hue Lampen'''
ip = "localhost:80" 
user = "newdeveloper"

#ip = "10.28.209.13:9001"
#user = "3dc1d8f23e55321f3c049c03ac88dff"

'''wandelt die angegebenen Orte in Geokoordinaten um. Diese werden als Angabe für die Methode RestData benoetigt. Die Geokoordinaten werden aus dem von der Rest-Schnittstelle zurueck gegebenen Json statisch ausgelesen'''
def changePlaceToGeoC(place):
    requestReturn = requests.get("https://geocoder.api.here.com/6.2/geocode.json?app_id={0}&app_code={1}&searchtext={2}".format(mapID, mapCode, place)).json()
    result = json.dumps(requestReturn)
    JsonString = json.loads(result)
    return [JsonString['Response']['View'][0]['Result'][0]['Location']['DisplayPosition']['Latitude'], JsonString['Response']['View'][0]['Result'][0]['Location']['DisplayPosition']['Longitude']]

'''holt von der Rest-Schnittstelle die Dauer der Fahrt und berechnet die Abfahrtszeit (gewuenschte Ankunftszeit - Dauer)'''
def mapRestDauerAbfahrtstart, stop, time):
    startpoint = changePlaceToGeoC(start)
    stoppoint = changePlaceToGeoC(stop)
    requestReturn = requests.get("https://route.api.here.com/routing/7.2/calculateroute.json?app_id={0}&app_code={1}&waypoint0=geo!{2},{3}&waypoint1=geo!{4},{5}&mode=fastest;car;traffic:enabled".format(mapID, mapCode, startpoint[0], startpoint[1], stoppoint[0], stoppoint[1])).json()
    result = json.dumps(requestReturn)
    JsonString = json.loads(result)
    json_tree = objectpath.Tree(JsonString['response'])
    result_tuple = tuple(json_tree.execute('$..travelTime'))
    dauer = max(result_tuple)
    save = extractTime(time)
    date = datetime(save[0], save[1], save[2], save[3], save[4], 00)
    return [dauer,date - timedelta(seconds=dauer)]

'''holt von der Rest-Schnittstelle die Dauer der Fahrt. Wird bei einem Update der Fahrt benoetigt'''
def mapRestNeueAnkunft(start, stop):
    startpoint = changePlaceToGeoC(start)
    stoppoint = changePlaceToGeoC(stop)
    requestReturn = requests.get("https://route.api.here.com/routing/7.2/calculateroute.json?app_id={0}&app_code={1}&waypoint0=geo!{2},{3}&waypoint1=geo!{4},{5}&mode=fastest;car;traffic:enabled".format(mapID, mapCode, startpoint[0], startpoint[1], stoppoint[0], stoppoint[1])).json()
    result = json.dumps(requestReturn)
    JsonString = json.loads(result)
    json_tree = objectpath.Tree(JsonString['response'])
    result_tuple = tuple(json_tree.execute('$..travelTime'))
    dauer = max(result_tuple)
    return extractTimeReverse(str(datetime.now() +  datetime.timedelta(seconds=dauer)))

'''erzeugt ein neues datetime Objekt'''
def extractTime(time):
    return (int(time[0:4]), int(time[5:7]), int(time[8:10]), int(time[11:13]), int(time[14:16]))
    
def extractTimeReverse(time):
    return str(int(time[0:4])) + "-" + str(int(time[5:7])) + "-" + str(int(time[8:10])) + "T" + str(int(time[11:13])) + ":" + str(int(time[14:16]))

'''Prueft ob die Rest-Schnittstell die uebergebene Postition kennt'''
def isPositionValid(place):
    requestReturn = requests.get("https://geocoder.api.here.com/6.2/geocode.json?app_id={0}&app_code={1}&searchtext={2}".format(mapID, mapCode, place)).json()
    JsonString = json.dumps(requestReturn)
    return "Result" in JsonString or "result" in JsonString

'''Methode die neue Daten in die Datenbank schreibt, wenn ein Fahrer neue Daten ueber einen Curl Befehl submitted. Prueft vorher ob die Angabe gueltig ist oder dem aktuellen Zustand wiederspricht'''
def readFromApi(result):
    try :
        jsn = json.loads(result)
        driver = jsn['Driver']
        status = jsn['Status']
        place = jsn['currentPlace']
        con = sqlite3.connect(DatabaseFile)
        curs = con.cursor()
        curs.execute("SELECT staff_number, Status, zielPointCurrentTour FROM driver")
        rows = curs.fetchall()
        for row in rows:
            if (int(driver) == int(row[0])):
                if (status == "driving" or status == "drivingNotInTime" or status == "waiting" or status == "inaktiv"):
                    if (isPositionValid(str(place)) == True):
                        if row[1] != "driving" and row[1] != "drivingNotInTime":
                            if status != "driving" and status != "drivingNotInTime":
                                newStatus(driver, status, place)
                                return okJson()
                            else:
                                return wrongJsonNoChange()
                        elif row[1] == "driving" or row[1] == "drivingNotInTime":
                            if status == "waiting" or status == "inaktiv":
                                newStatus(driver, status, place)
                            else:
                                try:
                                    updatePositionNeueAnkunft(place, row[2], driver)
                                except Exception as e:
                                    return wrongJsonPlace()
                            return okJson()
                    else:
                        return wrongJsonPlace()
                else:
                    return wrongJsonStatus()
        return wrongJsonDriver() 
    except Exception as e:
        print(traceback.format_exc())
        return wrongJson(e)

'''Methode um eine neue Position mitzuteilen. Neue Ankunftszeit wird festgelegt'''
def updatePositionNeueAnkunft(start, stop, driver):
    if (start != stop):
        con = sqlite3.connect(DatabaseFile)
        curs = con.cursor()
        curs.execute("SELECT targTime FROM driver WHERE staff_number = {}".format(driver)) 
        ro = curs.fetchone()
        estimatedArrivalTime = datetime.strptime(ro[0], '%Y-%m-%dT%H:%M') if ('T' in str(ro[0])) else datetime.strptime(ro[0], '%Y-%m-%d %H:%M:%S')
        startpoint = changePlaceToGeoC(start)
        stoppoint = changePlaceToGeoC(stop)
        calculatedTime = mapRestNeueAnkunft(start, stop)
        calculatedTime = datetime.strptime(calculatedTime, '%Y-%m-%dT%H:%M') if ('T' in str(calculatedTime)) else datetime.strptime(calculatedTime, '%Y-%m-%d %H:%M:%S')
        if (calculatedTime > estimatedArrivalTime): 
            enterDataWithStatus(start, startpoint[0], startpoint[1], stop, stoppoint[0], stoppoint[1], ro[0], driver, "drivingNotInTime", calculatedTime)    
            con.close()
            return "Not in Time"
        else:
            enterDataWithStatus(start, startpoint[0], startpoint[1], stop, stoppoint[0], stoppoint[1], ro[0], driver, "driving", calculatedTime)
            con.close()
            return "In Time"
    else:
        beendeFahrt()
        return "Finish Driving"

'''Hue Lampensteuerung'''
def Lampensteuerung(staff, state): 
    if str(state) == "inaktiv":
        requests.put("http://{0}/api/{1}/lights/{2}/state/".format(ip, user, int(staff)), data='{"on": false}')
    elif str(state) == "driving":
        requests.put("http://{0}/api/{1}/lights/{2}/state/".format(ip, user, int(staff)), data='{"on":true, "sat":254, "bri":254, "hue":7983}')
    elif str(state) == "waiting":
        requests.put("http://{0}/api/{1}/lights/{2}/state/".format(ip, user, int(staff)), data='{"on":true,"sat":254,"bri":254,"hue":25500}')
    elif str(state) == "drivingNotInTime":
        requests.put("http://{0}/api/{1}/lights/{2}/state/".format(ip, user, int(staff)), data='{"on" :true,"sat":254,"bri":254,"hue":65535}')
        time.sleep(1)
        requests.put("http://{0}/api/{1}/lights/{2}/state/".format(ip, user, int(staff)), data='{"on": false}')
    return None

'''aendert den Status und andere Daten in der Datenbank wenn die Fahrt beendet ist'''
def beendeFahrt():
    con = sqlite3.connect(DatabaseFile)
    curs = con.cursor()
    curs.execute("SELECT staff_number, Status, zielPointCurrentTour, actuallTime FROM driver")
    rows = curs.fetchall()
    x = 0
    for row in rows:
        if rows[x][1] == "driving" or rows[x][1] == "drivingNotInTime":
            if CurrentTimeEqualsDestinationTime(rows[x][0]) == True:
                newStatus(rows[x][0], "waiting", rows[x][2])
                print("CHANGED DRIVER: " + str(rows[x][0]))
            elif CurrentTimeEqualsDestinationTime(rows[x][0]) == None:
                pass
            elif CurrentTimeEqualsDestinationTime(rows[x][0]) == False:
                print("No changes yet")
        else:
            print("No change")
        x = x + 1
    con.commit()
    con.close()

'''prueft ob die aktuelle Zeit mit der gewuenschten Ankunftszeit uebereinstimmt.'''
def CurrentTimeEqualsDestinationTime(driver):
    con = sqlite3.connect(DatabaseFile)
    curs = con.cursor()
    curs.execute("SELECT staff_number, actuallTime FROM driver")
    arr = curs.fetchall()
    for row in arr:    
        if driver == row[0]:
            time = row[1]
            try:
                time = datetime.strptime(row[1], '%Y-%m-%dT%H:%M:%S')
            except Exception as e:
                try:
                    time = datetime.strptime(row[1], '%Y-%m-%dT%H:%M')
                except Exception as er:
                    try:
                        time = datetime.strptime(row[1], '%Y-%m-%d %H:%M')  
                    except Exception as erk:
                        try:
                            time = datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S') 
                        except Exception as exp:       
            if str(time) != 0 or str(time) != '00':
                var = timeBetweenStartAndStop(time - timedelta(seconds=20), time + timedelta(seconds=20), datetime.now())
                if var == True:
                    con.commit()
                    con.close()  
                    return True
            elif time == 0 or time == '00':
                pass
            else:
                print("ERROR")
    con.commit()
    con.close() 
    return False

'''prueft ob x zwischen start und stop liegt.'''
def timeBetweenStartAndStop(start, end, x):
    return True if (start <= end and start <= x <= end) else False

'''Methoden fuer den Zugriff auf die Datenbank'''

def newInputForDatabase(start, s_x, s_y, target, t_x, t_y, time, fahrer):
    con = sqlite3.connect(DatabaseFile)
    curs = con.cursor()
    curs.execute("UPDATE driver SET Status='{0}', startPointCurrentTour='{1}', s_x='{2}', s_y='{3}', zielPointCurrentTour='{4}', z_x='{5}', z_y='{6}', targTime='{7}', actuallTime='{9}' WHERE staff_number={8}".format("driving", start, s_x, s_y, target, t_x, t_y, time, int(fahrer), time))
    drive = curs.fetchone()
    con.commit()
    con.close() 

def newStatus(driver, status, place):
    print([driver,status,place])
    con = sqlite3.connect(DatabaseFile)
    curs = con.cursor()
    curs.execute("UPDATE driver SET Status='{0}', startPointCurrentTour='{1}', s_x='{2}', s_y='{3}', zielPointCurrentTour='{4}', z_x='{5}', z_y='{6}', targTime='{7}', actuallTime='{9}' WHERE staff_number={8}".format("inaktiv", "undef", "undef","undef", "undef", "undef", "undef", "00", int(driver), "00"))
    curs.execute("UPDATE driver SET Status='{}', currentPlace='{}' WHERE staff_number={}".format(str(status), str(place), int(driver)))
    drive = curs.fetchone()
    print("WORKED" + str(drive))
    con.commit()
    con.close()
    return True

def submitionStatus(driver):
    con = sqlite3.connect(DatabaseFile)
    curs = con.cursor()
    curs.execute("SELECT Status FROM driver WHERE staff_number = {}".format(driver))
    print("DRIVER: " + str(driver))
    row = curs.fetchone()
    print("ROW: " + str(row))
    con.commit()
    con.close()
    if row[0] == "waiting":
        return True
    else:
        return False


def enterDataWithStatus(start, s_x, s_y, target, t_x, t_y, time, fahrer, status, timetwo):
    con = sqlite3.connect(DatabaseFile)
    curs = con.cursor()
    curs.execute("UPDATE driver SET Status='{0}', startPointCurrentTour='{1}', s_x='{2}', s_y='{3}', zielPointCurrentTour='{4}', z_x='{5}', z_y='{6}', targTime='{7}', actuallTime='{9}' WHERE staff_number={8}".format(status, start, s_x, s_y, target, t_x, t_y, time, int(fahrer), timetwo))
    drive = curs.fetchone()
    con.commit()
    con.close()

'''JSON'''

def wrongJsonNoChange():
    return json.loads('{"error": [{"taxifahrer": "korrekt", "status": "ungueltiger Status","aktuellerStandort": "korrekt","Comment": "der Status darf im Moment nicht geaendert werden"}]}')

def wrongJson(ex):
    return json.loads('{"error": [{"taxifahrer": "korrekt","status": "korrekt","aktuellerStandort": "korrekt","Comment": "es wird ein JSON benoetigt"}]}')

def wrongJsonDriver():
    return json.loads('{"error": [{"taxifahrer": "Taxifahrer existiert nicht","status": "korrekt","aktuellerStandort": "korrekt"}]}')

def okJson():
    return json.loads('{"success": [{"taxifahrer": "korrekt","status": "korrekt","aktuellerStandort": "korrekt"}]}')

def wrongJsonStatus():
    return json.loads('{"error": [{"taxifahrer": "korrekt","status": "ungueltiger Status","aktuellerStandort": "korrekt"}]}')

def wrongJsonPlace():
    return json.loads('{"error": [{"taxifahrer": "korrekt","status": "korrekt","aktuellerStandort": "Ort existiert nicht"}]}')