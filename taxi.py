from flask import Flask, render_template, request, json,jsonify
import sqlite3
from API_REC_TRANS import *
import datetime
from datetime import datetime

app = Flask(__name__)

Database = 'drivers.sqlite3'

@app.route("/", methods = ['POST', 'GET'])
def hello():
    if request.method == 'POST':
        result = request.form
        start = result['textfield']
        stop = result['textfield2']
        time = result['textfield3']
        fahr = result['fahr']
        stat = submitionStatus(fahr)
        tup = extractTime(time)
        time2 = datetime(tup[0], tup[1], tup[2], tup[3], tup[4], 00)
        if time2 >= datetime.now():
            print(stat)
            if stat == True:
                print("haha")
                startpoint = cood(start)
                stoppoint = cood(stop)
                apiData = mapRestDauerAbfahrt(start, stop, time)
                newInputForDatabase(start, startpoint[0], startpoint[1], stop, stoppoint[0], stoppoint[1], time, fahr)
                Lampensteuerung(fahr,"driving")
                return render_template('index.html',text=start, text2=stop, text3=time, fahr=driver(fahr), apidate=apiData)
            else:
                return render_template('index.html', textelse="Taxi fahrer ist momentan am fahren kann die fahrt nicht annehmen!")
        else:
            return render_template('index.html', textelse="Die Zeit muss in der Zukunft liegen")
    else:
        return render_template('index.html')



@app.route("/api", methods = ['POST', 'PUT'])
def api():
    if request.method == 'POST':
        result = request.get_json()
        try:
            print("GO")
            return jsonify(readFromApi(json.dumps(result)))
        except Exception as e:
            return "UNKWOWN JSON"
    elif request.method == 'PUT':
        result = request.get_json()
        try:
            return jsonify(readFromApi(json.dumps(result)))
        except Exception as e:
            print(e)
            return "UNKWOWN JSON"
    return "Wrong Method"


@app.route("/track", methods = ['POST', 'GET'])
def trackDriver():
    if request.method == 'POST':
        result = request.form
        connection_ = sqlite3.connect(Db_File_Name)
        cursor_ = connection_.cursor()
        fahr = result['fahr']
        if fahr == None:
            return render_template('track.html', title="Kein Ergebnis")
        cursor_.execute("SELECT * FROM driver WHERE staff_number={} ".format(int(fahr)))
        drive = cursor_.fetchone()
        connection_.commit()
        connection_.close() 
        return render_template('track.html', title=fahr, name=drive[1], status=drive[2], cP=drive[3],start=drive[4],sx=drive[5],sy=drive[6],ziel=drive[7],zx=drive[8], zy=drive[9], time=drive[10])
    return render_template('track.html')

if __name__ == '__main__':
    app.run(debug=True)