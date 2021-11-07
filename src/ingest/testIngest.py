from os import curdir
import psycopg2

import csv
import datetime

conn = psycopg2.connect("dbname=covardb user=covardbapps")
cur = conn.cursor()

with open("tests.csv", newline='') as csvFile:
    cReader = csv.reader(csvFile, delimiter=',')
    for row in cReader:
        print(','.join(row))

        if not row[0] == "DATE":
            date = datetime.date.fromisoformat(row[0])
            personUID = row[1]
            infected = row[2] == "true"

            cur.execute("INSERT INTO tests(dateval, personaluid, infected) VALUES (%s, %s, %s)", (
                date, personUID, infected
            ))

            conn.commit()

cur.close()
conn.close()