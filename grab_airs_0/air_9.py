from grab import Grab
import json

g = Grab(connect_timeout=50, timeout=50)

SCHEDULED = "scheduled"
ARRIV_ = "arriv?"
LANDED = "landed"
D_COLL_ = "d?coll?"
ANNUL = "annul?"
CANCELLED = "cancelled"
ENREGISTREMENT_FERM = "Enregistrement Ferm?"
DEPARTED = "departed"
EMBARQUEMENT = "embarquement"
BOARDING = "boarding"
ENREGISTREMENT_OUVERT = "enregistrement ouvert"
CHECKIN = "checkin"
TERMIN_ = "termin?"
RETARD_ = "retard?"
DELAYED = "delayed"


def fixStatus(status):
    return {
        ARRIV_:LANDED,
        D_COLL_:DEPARTED,
        ENREGISTREMENT_OUVERT:CHECKIN,
        EMBARQUEMENT:BOARDING,
        TERMIN_:CANCELLED,
        RETARD_:DELAYED,
        ENREGISTREMENT_FERM:BOARDING,
        ANNUL:CANCELLED
    }.get(status, "")

def getDataFromDocumentCMN(flight):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""
    codeShares = []

    try:
        arFlightno = str(flight['num_vol']).split(" / ")
        flightno = arFlightno[0]
        if len(arFlightno) > 1:
            for i in range(1, len(arFlightno)):
                codeShares.append(arFlightno[i])
    except:
        flightno = ""
    try:
        scheduled = flight['date_vol'] + " " + flight['heure_vol'] + ":" + flight['min_vol']

        estimated = scheduled
    except:
        scheduled = ""

    try:
        rawStatus = str(flight['Observation'])
        lowerRawStatus = str.lower(rawStatus)
        status = fixStatus(lowerRawStatus)
    except:
        status = ""

    if len(status) <= 0:
        status = SCHEDULED

    result = {
        "flightno": flightno,
        "scheduled": scheduled,
        "status": status,
        "raw_status": rawStatus
    }

    if estimated != "":
        result["estimated"] = estimated
    if len(codeShares) > 0:
        result["codeshares"] = codeShares
    return result


departures = []
arrivals = []

urlCMN = "http://www.onda.ma/layout/set/ajax/onda_horaires/get_list"
resp = g.go(urlCMN, post={'type': 'arrivees', 'codeAeroport' : 'CMN'})
jsonResponse = json.loads(resp.body)
for arHours in jsonResponse:
    flightPerHour = jsonResponse[arHours]
    for flight in flightPerHour:
        arrival = getDataFromDocumentCMN(flight)
        arrivals.append(arrival)

urlCMN = "http://www.onda.ma/layout/set/ajax/onda_horaires/get_list"
resp = g.go(urlCMN, post={'type': 'departs', 'codeAeroport' : 'CMN'})
jsonResponse = json.loads(resp.body)
for arHours in jsonResponse:
    flightPerHour = jsonResponse[arHours]
    for flight in flightPerHour:
        departure = getDataFromDocumentCMN(flight)
        departures.append(departure)

resultCMN = {}
resultCMN["airport_id"] = "CMN"
resultCMN["departures"] = departures
resultCMN["arrivals"] = arrivals
jsonResultCMN = json.dumps(resultCMN)
print jsonResultCMN