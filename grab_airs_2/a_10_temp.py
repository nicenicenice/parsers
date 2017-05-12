from grab import Grab
import json
from datetime import datetime, timedelta
import re

#PER Perth Airport Perth https://www.perthairport.com.au/flights/departures-and-arrivals?Nature=Departure

#19%19

UNKNOWN = "unknown"
CHECK_IN = "check-in"
BOARDING_CLOSED = "boarding closed"
ON_TIME = "on-time"

CANCELED = "canceled"
AIRBORNE = "airborne"
ESTIMSTED = "estimated"

ARRIVED = "arrived"
LATE = "late"
LAST_CALL = "last call"
GATE_CLOSED = "gate closed"
FINAL_CALL = "final call"
GATE_OPEN = "gate open"

SCHEDULED = "scheduled"
DELAYED = "delayed"
CANCELLED = "cancelled"
CHECKIN = "checkin"
BOARDING = "boarding"
OUTGATE = "outgate"
DEPARTED = "departed"
EXPECTED = "expected"
LANDED = "landed"

datePattern = "%Y-%m-%d %H:%M:%S"
nowTime = datetime.now()
departures = []
arrivals = []

def fixStatus(status):
    return {
        SCHEDULED: SCHEDULED,
        DELAYED: DELAYED,
        CANCELLED: CANCELLED,
        CHECKIN: CHECKIN,
        BOARDING: BOARDING,
        OUTGATE: OUTGATE,
        DEPARTED: DEPARTED,
        EXPECTED: EXPECTED,
        LANDED: LANDED,

        CHECK_IN:CHECKIN,
        ESTIMSTED:EXPECTED,
        AIRBORNE: DEPARTED,
        CANCELED:CANCELLED,
        BOARDING_CLOSED:OUTGATE,
        ON_TIME:SCHEDULED,
        GATE_CLOSED:OUTGATE,
        FINAL_CALL:BOARDING,
        GATE_OPEN:BOARDING,
        ARRIVED:LANDED,
        LATE: DELAYED,
        "":SCHEDULED
    }.get(status, UNKNOWN)

def getFullDate(hourMinute, scheduleDateTime):
    datePattern = "%Y-%m-%d %H:%M:%S"
    nowTime = datetime.now()
    correctDate = scheduleDateTime

    h = int(hourMinute[:2])
    m = int(hourMinute[3:])

    notFormatedTime = correctDate.replace(hour=h, minute=m, second=0)

    if scheduleDateTime.hour > 20 and h < 5:
        notFormatedTime = notFormatedTime + timedelta(days=1)
    elif scheduleDateTime.hour < 5 and h > 20:
        notFormatedTime = notFormatedTime - timedelta(days=1)

    formatedTime = notFormatedTime.strftime(datePattern)
    return formatedTime

def getDataFromDocumentPER(flight, dateTime, isDeparture=False):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""
    codeshares = []
    terminal = ""
    luggage = ""
    gate = ""

    try:
        codeshares = flight['codeShares']
    except:
        codeshares

    try:
        rawStatus = str(flight['Remark'])
        rawStatus = str.lower(rawStatus).strip()
        status = fixStatus(rawStatus)
        if status == "":
            status = UNKNOWN
    except:
        status = ""

    try:
        flightno = str(flight['FlightNumber'])
    except:
        flightno = ""

    try:
        rawScheduled = flight['ScheduledTime']
        h = int(rawScheduled[:2])
        m = int(rawScheduled[3:])
        scheduleDateTime = dateTime.replace(hour=h, minute=m, second=0)
        scheduled = scheduleDateTime.strftime(datePattern)
    except:
        scheduled = ""

    try:
        rawAddTime = flight['EstimatedTime']
        addTime = getFullDate(rawAddTime, scheduleDateTime)
        if status == LANDED or status == DEPARTED:
            actual = addTime
        else:
            estimated = addTime
    except:
        actual = ""
        estimated = ""
        addTime = ""

    try:
        terminal = flight['Terminal']
    except:
        terminal = ""

    if isDeparture:
        try:
            gate = flight['Gate']
        except:
            gate = ""

    result = {
        "flightno": flightno,
        "scheduled": scheduled,
        "status": status,
        "raw_status": rawStatus
    }

    if len(codeshares) > 0:
        result["codeshares"] = codeshares
    if terminal != "":
        result["terminal"] = terminal
    if luggage != "":
        result["luggage"] = luggage
    if gate != "":
        result["gate"] = gate
    if estimated != "":
        result["estimated"] = estimated
    if actual != "":
        result["actual"] = actual
    return result


g = Grab(connect_timeout=90, timeout=90)
"""g.setup(headers={
    "X-Requested-With":"XMLHttpRequest",
    "Cookie":"__RequestVerificationToken=6xXvZkJFnC2p_angIKyJbMrFDKmiJqBDxlqmOX1TUYRwKjAz_ZVJDhMe2stmSwwlx2d_Q41lXg7h_M5OusaEtWyn2PY1;"
})"""

url = "https://www.perthairport.com.au/flights/departures-and-arrivals?Nature=Departure"
tomorrowDateTime = nowTime + timedelta(days=1)


resp = g.go(url)
today = g.doc.select("//*[@id='day']/option[1]/@value").text()
tomorrow = g.doc.select("//*[@id='day']/option[2]/@value").text()
__RequestVerificationToken = g.doc.select("//*[@id='flightSearch']/input/@value").html()

dateSelectPattern = "%m/%d/%Y"
todayDateTime = datetime.strptime(today, dateSelectPattern)
tomorrowDateTime = datetime.strptime(tomorrow, dateSelectPattern)
#Nature:Arrivals
#Nature:Departures

postParams = {
    "scController":"Flights",
    "scAction":"GetFlightResults",
    "Date":today,
    "Time":"",
    "Nature":"Arrivals",
    "DomInt":"",
    "Query":"",
    "Terminal":"",
    "__RequestVerificationToken":__RequestVerificationToken
}

resp = g.go(url, post=postParams)
jsonResponse = json.loads(resp.body)

for flight in jsonResponse['Results']:
    arrival = getDataFromDocumentPER(flight, todayDateTime)
    arrivals.append(arrival)

postParams = {
    "scController":"Flights",
    "scAction":"GetFlightResults",
    "Date":today,
    "Time":"",
    "Nature":"Departures",
    "DomInt":"",
    "Query":"",
    "Terminal":"",
    "__RequestVerificationToken":__RequestVerificationToken
}

resp = g.go(url, post=postParams)
jsonResponse = json.loads(resp.body)

for flight in jsonResponse['Results']:
    departure = getDataFromDocumentPER(flight, todayDateTime)
    departures.append(departure)


"""
startUrl = "https://www.perthairport.com.au/flights/departures-and-arrivals/"

for i in range(len(departures) - 1):
    url = startUrl + str.lower(departures[i]["flightno"])+ str(todayDateTime.year)+ "0" + str(todayDateTime.month)+ "0" + str(todayDateTime.day) + "d"
    resp = g.go(url)
    try:
        gate = g.doc.select("/html/body/div/div[4]/div/div/div/div[2]/div/div/div[2]/div[1]/div/div[2]/div/div[2]/p[2]").html()
        print gate
    except:
        pass
    #https://www.perthairport.com.au/flights/departures-and-arrivals/od15620170509d
"""

resultPER = {}
resultPER["airport_id"] = "PER"
resultPER["departures"] = departures
resultPER["arrivals"] = arrivals

jsonResult = json.dumps(resultPER)
print jsonResult
