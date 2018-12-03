import sqlite3,sys
from time import sleep

'''Datenbank fuer Taxifahrer'''
DatabaseFile = "t4.sqlite3"

'''leert die Datenbank'''
def dropTable():
    con = sqlite3.connect(DatabaseFile)
    curs = con.cursor()
    curs.execute(""" DROP TABLE IF EXISTS driver; """)
    con.commit()
    con.close()

'''initialisiert die Datenbank mit gueltigen Startwerten'''
def dataBaseTableCreater():
    con = sqlite3.connect(DatabaseFile)
    curs = con.cursor()
    curs.execute('''CREATE TABLE IF NOT EXISTS driver (staff_number INTEGER PRIMARY KEY, Name text,  Status text, currentPlace text, startPointCurrentTour text, s_x text,  s_y text, zielPointCurrentTour text, z_x text, z_y text, targTime text, actuallTime text);''')                                                                                                                                        # ID Name Status currentPlace startPointCurrentTour s_x s_y zielPointCurrentTour z_x z_y
    curs.execute('''INSERT INTO driver (Name, Status, currentPlace, startPointCurrentTour, s_x, s_y, zielPointCurrentTour, z_x, z_y, targTime, actuallTime) VALUES ('John Sommer', 'waiting','munich', 'undef','undef', 'undef', 'undef', 'undef', 'undef', '00', '00')''')
    curs.execute('''INSERT INTO driver (Name, Status, currentPlace, startPointCurrentTour, s_x, s_y, zielPointCurrentTour, z_x, z_y, targTime, actuallTime) VALUES ('Hanna Frühling', 'waiting','hamburg', 'undef','undef', 'undef', 'undef', 'undef', 'undef', '00', '00')''')
    curs.execute('''INSERT INTO driver (Name, Status, currentPlace, startPointCurrentTour, s_x, s_y, zielPointCurrentTour, z_x, z_y, targTime, actuallTime) VALUES ('Herbert Winter', 'waiting','berlin', 'undef','undef', 'undef', 'undef', 'undef', 'undef', '00', '00')''')
    curs.execute("SELECT * FROM driver")
    con.commit()
    con.close()
 
'''gibt die aktuelle Datenbank aus''' 
def showTable():
    con = sqlite3.connect(DatabaseFile)
    curs = con.cursor()
    curs.execute("SELECT * FROM driver")
    rows = curs.fetchall()
    for row in rows:
        print(">> ROW IN TABLE >> " + str(row))
    con.commit()
    con.close()

#dropTable()
#dataBaseTableCreater()
showTable()