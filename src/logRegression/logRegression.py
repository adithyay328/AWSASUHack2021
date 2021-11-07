import random
import math

#GENERATION PHASE
#There are 3 inputs in this model: 
# 1. Days since infected for host
# 2. Duration of interaction
# 3. Proximity of interaction

#THE NEXT 3 FUNCTIONS TAKE IN A PARAMETER AND RETURN A FLOAT OUTPUT BETWEEN 0 AND 100, with 100 indicating a high chance of infection
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

#Input and output arrays
x = []
y = []

for i in range(0, 100000):
    daysSinceInfectedForHost = random.randint(1, 14)
    durationOfInteractionMinutes = random.randint(1, 75)
    proximityOfInteraction = random.randint(1, 10)

    scaledChanceFromDate = scaleDaysSinceInfectedForHost(daysSinceInfectedForHost)
    scaledDuration = scaleDurationOfInteractionMinutes(durationOfInteractionMinutes)
    scaledProxim = scaleProximityOfInteraction(proximityOfInteraction)

    #In the real world, there are a lot of variables that affect how different factors affect the end result. For that reason, we're using
    #RNG to add some unpredictability to the scaled variables
    scaledChanceFromDate *= ( random.randint(75, 125) / 100)
    scaledDuration *= ( random.randint(75, 125) / 100)
    scaledProxim *= ( random.randint(75, 125) / 100)

    x.append(scaledChanceFromDate)
    x.append(scaledDuration)
    x.append(scaledProxim)

    resultSum = scaledChanceFromDate + scaledDuration + scaledProxim

    resultSum *= ( random.randint(75, 125) / 100)

    isPositive = resultSum > 250
    y.append(isPositive)

    print(f"{scaledChanceFromDate}; {scaledDuration}; {scaledProxim}; {resultSum}; {isPositive}")

#REGRESSION PHASE
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

xNP = np.array(x).reshape(-1, 3)
yNP = np.array(y).reshape(-1, 1)

xNPTrain, xNPTest, yNPTrain, yNPTest = train_test_split(xNP, yNP, test_size=0.3)

# all parameters not specified are set to their defaults
logisticRegr = LogisticRegression()

logisticRegr.fit(xNPTrain, yNPTrain.ravel())
score = logisticRegr.score(xNPTest, yNPTest)
print(score)