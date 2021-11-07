#In this module, we'll connect to the SQL database in order to quickly traverse our population and create our mock data. While this kinda 
#feels like cheating, the whole point of this is to generate a CSV at the end, which can then be fed into our ingest and sim components.
#In a real environment, the CSV would be derived from real world data
import numpy as np
from sklearn.linear_model import LogisticRegression
import psycopg2

import csv
import uuid
import random
from datetime import date, timedelta
import datetime
import pickle
import math

conn = psycopg2.connect("dbname=covardb user=covardbapps")
cur = conn.cursor()

TOTALNUMOFPEOPLE = 1000
NUMOFINFECTED = 5

#Loading trained regression model from disk
logisticRegr = pickle.load(open("trainedModel.sav", "rb"))

#Getting CSV files ready to write
peopleCSVFile = open("people.csv", "w", newline="")
peopleCWriter = csv.writer(peopleCSVFile)

testsCSVFile = open("tests.csv", "w", newline="")
testsCWriter = csv.writer(testsCSVFile)

interactionsCSVFile = open("interactions.csv", "w", newline="")
interactionsCWriter = csv.writer(interactionsCSVFile)

#30 days back from today is our start date
startDateOfSimulation = datetime.date.today() - datetime.timedelta(days=30)


#Writing our hints rows
peopleCWriter.writerow(["INFECTED", "UID", "DAYS SINCE INFECTION", "AGE", "MEDICAL CONIDTION"])
testsCWriter.writerow(["DATE", "PERSONUID", "INFECTED"])
interactionsCWriter.writerow(["DATE", "IDONE", "IDTWO", "DURATION", "PROXIMITY"])

def insertPersonIntoPeopleTable(uid, age, infected, daysSinceInfection, medicalCondition):
    cur = conn.cursor()

    cur.execute("INSERT INTO people(uid, infected, dayssinceinfection, age, medicalconditions) VALUES (%s, %s, %s, %s, %s);", (
            uid, infected, daysSinceInfection, age, medicalCondition
    ))

    conn.commit()

def writePersonToPeopleCSV(uid, age, infected, daysSinceInfection, medicalCondition):
    peopleCWriter.writerow([infected, uid, daysSinceInfection, age, medicalCondition])

def insertTestIntoTestsTable(dateVal, personUID, infected):
    cur = conn.cursor()

    cur.execute("INSERT INTO tests(dateval, personuid, infected) VALUES (%s, %s, %s);", (
        dateVal, personUID, infected
    ))

    conn.commit()

def writeTestToTestCSV(dateVal, personUID, infected):
    testsCWriter.writerow([dateVal, personUID, infected])

def insertInteractionIntoInteractionsTable(uidOne, uidTwo, dateVal, duration, proximity):
    cur = conn.cursor()

    cur.execute("INSERT INTO interactions(idone, idtwo, dateval, duration, proximity) VALUES(%s, %s, %s, %s, %s);", (
        uidOne, uidTwo, dateVal, duration, proximity
    ))

    conn.commit()
    cur.close()

def writeInteractionToInteractionCSV(uidOne, uidTwo, dateVal, duration, proximity):
    interactionsCWriter.writerow([dateVal, uidOne, uidTwo, duration, proximity])


#Creating our population
for i in range(0, NUMOFINFECTED):
    uid = uuid.uuid1()
    age = random.randint(14, 70)
    infected = True
    daysSinceInfection = random.randint(1, 12)
    medicalCondition = random.randint(1, 10)

    insertPersonIntoPeopleTable(uid.hex, age, infected, daysSinceInfection, medicalCondition)
    writePersonToPeopleCSV(uid.hex, age, infected, daysSinceInfection, medicalCondition)

    for i in range(0, daysSinceInfection + 1):
        dateVal = startDateOfSimulation - timedelta(days=i)
        insertTestIntoTestsTable(dateVal, uid.hex, infected)
        writeTestToTestCSV(dateVal, uid.hex, infected)

for i in range(0, TOTALNUMOFPEOPLE - NUMOFINFECTED):
    uid = uuid.uuid1()
    age = random.randint(14, 70)
    infected = False
    daysSinceInfection = -1
    medicalCondition = random.randint(1, 10)

    insertPersonIntoPeopleTable(uid.hex, age, infected, daysSinceInfection, medicalCondition)
    writePersonToPeopleCSV(uid.hex, age, infected, daysSinceInfection, medicalCondition)

    insertTestIntoTestsTable(startDateOfSimulation, uid.hex, infected)
    writeTestToTestCSV(startDateOfSimulation, uid.hex, infected)


class Person:
    def __init__(self, uid, infected, daysSinceInfection, age, medicalCondition):
        self.uid = uid
        self.infected = infected
        self.daysSinceInfection = daysSinceInfection
        self.age = age
        self.medicalCondition = medicalCondition

    @staticmethod
    def get(uidVal):
        cur = conn.cursor()

        cur.execute("SELECT uid, infected, dayssinceinfection, age, medicalconditions FROM people WHERE uid=%s", (uidVal,))

        result = cur.fetchone()

        newPerson = Person(result[0], result[1], result[2], result[3], result[4])
        return newPerson
    
    def update(self):
        cur = conn.cursor()

        cur.execute("UPDATE people SET infected=%s, dayssinceinfection=%s WHERE uid=%s;", ( self.infected, self.daysSinceInfection , self.uid) )

    @staticmethod
    def getAllInfectedOnAGivenDate(dateVal):
        cur = conn.cursor()

        cur.execute("SELECT personuid FROM tests WHERE dateval=%s AND infected='t';", (dateVal,))

        result = cur.fetchall()

        personObjs = [Person.get(resultRow[0]) for resultRow in result]

        return personObjs
    
    @staticmethod
    def getPeopleThatNeedUninfection():
        cur = conn.cursor()

        cur.execute("SELECT uid FROM people WHERE dayssinceinfection=14;")
        result = cur.fetchall()

        personObjs = [Person.get(resultRow[0]) for resultRow in result]

        return personObjs


#We're going to create interactions for our infected population; the rest aren't strictly necessary,
#since it makes no difference if there's an interaction between 2 non-infected people. This is also going to be true
#for the predictive component

#We're going to start at the start date of our simulation, and work our way to today. We'll assume that every
#infected person has 2 interactions per day
def getRandomNonInfectedUID():
    cur = conn.cursor()

    print("Running")
    offset = (random.randint(1, TOTALNUMOFPEOPLE - NUMOFINFECTED - 2))

    sqlCommand = f"SELECT uid FROM people WHERE NOT infected OFFSET { offset } LIMIT 1;"
    print(sqlCommand)
    cur.execute(sqlCommand)

    result = cur.fetchall()
    print(result)

    cur.close()
    conn.commit()

    return result[0]

def getDaysSinceInfectedForUID(uidVal):
    cur = conn.cursor()

    cur.execute("SELECT dayssinceinfection FROM people WHERE uid=%s;", (uidVal,))
    result = cur.fetchall()

    return result[0][0]

def scaleDaysSinceInfectedForHost(days):
    incubationPeriod = random.randint(2, 14)

    x = days
    n = incubationPeriod

    #100 means that someone is at their maximum infectivity; 50 means they're at half of their maximum infectivity
    relativeProbabilityOfInfection = ( (-1 / n) * ( ( x - n ) ** 2 )  + n ) / n * 100
    
    return max(relativeProbabilityOfInfection, 0)

def scaleDurationOfInteractionMinutes(durationMins):
    x = durationMins

    probability = ( math.e ** (1/8)*x ) - .5

    scaled = probability * 8.30426839395

    return min(scaled, 100)

def scaleProximityOfInteraction(prox):
    return prox ** 2

currSimulationDate = startDateOfSimulation
while currSimulationDate <= datetime.date.today():
    #These are people who have had covid at the 2 week mark. They are no longer really infected, but this needs to be
    #updated in the db
    needToBeUninfected = Person.getPeopleThatNeedUninfection()
    for person in needToBeUninfected:
        person.daysSinceInfection = -1
        person.infected  = False
        person.update()

        insertTestIntoTestsTable(currSimulationDate, person.uid, person.infected)

    currentlyInfected = Person.getAllInfectedOnAGivenDate(currSimulationDate)

    print(len(currentlyInfected))
    for person in currentlyInfected:
        #2 interactions per day per infected person
        for i in range(0, 2):
            nonInfectedUID = getRandomNonInfectedUID()
            duration = random.randint(1, 75)
            proximity = random.randint(1, 10)

            insertInteractionIntoInteractionsTable(person.uid, nonInfectedUID, currSimulationDate, duration, proximity)

            #Logistic regression component
            regressionInputs = []

            #These are in the same order as the regression algo was initially trained on
            regressionInputs.append(scaleDaysSinceInfectedForHost(person.daysSinceInfection))
            regressionInputs.append(scaleDurationOfInteractionMinutes(duration))
            regressionInputs.append(scaleProximityOfInteraction(proximity))

            inputNp = np.array(regressionInputs).reshape(-1, 3)

            infected = logisticRegr.predict(inputNp)[0]

            if infected:
                nonInfected = Person.get(nonInfectedUID)
                nonInfected.infected = True
                nonInfected.daysSinceInfection = 1
                nonInfected.update()

                insertTestIntoTestsTable(currSimulationDate, nonInfected.uid, True)
        
        person.daysSinceInfection = person.daysSinceInfection + 1
        person.update()

    currSimulationDate += datetime.timedelta(days=1)

cur.close()
conn.close()