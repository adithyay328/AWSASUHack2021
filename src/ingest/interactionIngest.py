import datetime
from os import curdir
import psycopg2

import csv

conn = psycopg2.connect("dbname=covardb user=covardbapps")
cur = conn.cursor()

with open("interactions.csv", newline='') as csvFile:
    cReader = csv.reader(csvFile, delimiter=',')
    for row in cReader:
        print(','.join(row))

        if not row[0] == "DATE":

            date = datetime.date.fromisoformat(row[0])
            uidOne = row[1]
            uidTwo = row[2]
            duration = int(row[3])
            proximity = int(row[4])

            cur.execute("INSERT INTO interactions(idone, idtwo, dateval, duration, proximity) VALUES (%s, %s, %s, %s, %s)", (
                uidOne, uidTwo, date, duration, proximity
            ))

            conn.commit()

cur.close()
conn.close()