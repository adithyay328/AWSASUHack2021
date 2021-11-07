from os import curdir
import psycopg2

import csv

conn = psycopg2.connect("dbname=covardb user=covardbapps")
cur = conn.cursor()

with open("example.csv", newline='') as csvFile:
    cReader = csv.reader(csvFile, delimiter=',')
    for row in cReader:
        print(','.join(row))

        if not row[0] == "INFECTED":
            infected = row[0] == "true"
            uid = row[1]
            daysInfected = int(row[2])
            age = int(row[3])
            medicalCond = int(row[4])

            cur.execute("INSERT INTO people(uid, infected, dayssinceinfection, age, medicalconditions) VALUES (%s, %s, %s, %s, %s)", (
                uid, infected, daysInfected, age, medicalCond
            ))

            conn.commit()

cur.close()
conn.close()