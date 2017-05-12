# -*- coding: utf-8 -*-

from grab import Grab
import json
import time
import re
from datetime import datetime, timedelta

g = Grab(connect_timeout=90, timeout=90)

ARRIVAL = "arrival"
ON_SCHEDULE = "on schedule"
UNKNOWN = "unknown"
EARLY_ARRIVAL = "early arrival"


CHECK_IN = "check-in"
BOARDING_CLOSED = "boarding closed"
ON_TIME = "on time"
CANCELED = "canceled"
AIRBORNE = "airborne"
EN_ROUTE = "en route"

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

        EARLY_ARRIVAL:SCHEDULED,
        ON_SCHEDULE:SCHEDULED,
        ARRIVAL:LANDED,
        CHECK_IN:CHECKIN,
        EN_ROUTE:EXPECTED,
        AIRBORNE: DEPARTED,
        CANCELED:CANCELLED,
        BOARDING_CLOSED:OUTGATE,
        ON_TIME:SCHEDULED,
        GATE_CLOSED:OUTGATE,
        FINAL_CALL:BOARDING,
        GATE_OPEN:BOARDING,
        ARRIVED:LANDED,
        LATE: DELAYED
    }.get(status, "")

departures = []
arrivals = []
datePattern = "%Y-%m-%d %H:%M:%S"
nowTime = datetime.now()

def getFormatedCheckinDesks(checkinStr):
    if checkinStr.find(",") > 0:
        arDesks = checkinStr.split(",")
        match = re.search("([a-zА-Я])", checkinStr)
        if not match:
            arDesks.sort(key=int)
        else:
            arDesks.sort()
        return arDesks[0] + " - " + arDesks[len(arDesks) - 1]
    else:
        return checkinStr

def getDataFromDocumentVVO(el):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""
    codeShares = []
    gate = ""
    day = ""
    trId = ""
    terminal = ""
    check_in_desks = ""
    city = ""

    try:
        trId = el.select('./@id').text()
    except:
        trId = ""

    try:
        try:
            flightno = commonJson[trId]["Flight number"]
        except:
            flightno = el.select('.//td[1]').text()
        flightno = flightno.encode("utf-8")

    except:
        flightno = ""
    try:
        city = commonJson[trId]["Planning route"]
    except:
        city = ""

    try:
        rawTerminal = commonJson[trId]["Terminal"]
        rawTerminal = rawTerminal.encode("utf-8")
        if rawTerminal.find(" ") > 0:
            terminal = rawTerminal[:rawTerminal.find(" ")]
        else:
            terminal = rawTerminal
    except:
        terminal = ""

    try:
        rawCheckInDesks = commonJson[trId]["Number check-in desk"]
        check_in_desks = rawCheckInDesks.encode("utf-8")
        #check_in_desks = getFormatedCheckinDesks(rawCheckInDesks)
    except:
        check_in_desks = ""

    try:
        rawActual = commonJson[trId]["Actual time"]
        actualDateTime = datetime.strptime(rawActual, "%b %d, %Y, %H:%M")
        actual = actualDateTime.strftime(datePattern)
    except:
        actual = ""

    try:
        try:
            rawScheduled = commonJson[trId]["Time schedule"]
            scheduleDateTime = datetime.strptime(rawScheduled, "%b %d, %Y, %H:%M")
        except:
            rawScheduled = el.select('.//td[4]').text() + " " + str(nowTime.year)
            scheduleDateTime = datetime.strptime(rawScheduled, "%b %d, %H:%M %Y")

        scheduled = scheduleDateTime.strftime(datePattern)
    except:
        scheduled = ""

    try:
        try:
            rawStatus = str(commonJson[trId]["Status"])
        except:
            rawStatus = str(el.select('.//td[5]').text())
        rawStatus = str.lower(rawStatus)
        status = fixStatus(rawStatus)
        if status == "":
            status = UNKNOWN
    except:
        rawStatus = ""
        status = ""

    if status == "":
        status = SCHEDULED

    result = {
        "flightno": flightno,
        "scheduled": scheduled,
        "status": status,
        "raw_status": rawStatus
    }
    if city != "":
        result["city"] = city
    if check_in_desks != "":
        result["check_in_desks"] = check_in_desks
    if terminal != "":
        result["terminal"] = terminal
    if actual != "":
        result["actual"] = actual
    return result

currentTimeStamp = int(round(time.time()))

urlVVO = "http://vvo.aero/en/ajax/table-today-2.html?_=" + str(currentTimeStamp)

resp = g.go(urlVVO)


scriptCodeArrival = g.doc.select('//*[@id="arrival"]/script').text()
scriptCodeDeparture = g.doc.select('//*[@id="departure"]/script').text()

# arrival
IdxBeginOfJsonArrival = scriptCodeArrival.find(", {\"") + 2
IdxEndOfJsonArrival = len(scriptCodeArrival) - 2

jsonResponseArrival = scriptCodeArrival[IdxBeginOfJsonArrival:IdxEndOfJsonArrival]
jsonResponseObjArrival = json.loads(jsonResponseArrival)

# departure
IdxBeginOfJsonDeparture = scriptCodeDeparture.find(", {\"") + 2
IdxEndOfJsonDeparture = len(scriptCodeDeparture) - 2

jsonResponseDeparture = scriptCodeDeparture[IdxBeginOfJsonDeparture:IdxEndOfJsonDeparture]
jsonResponseObjDeparture = json.loads(jsonResponseDeparture)

commonJson = jsonResponseObjArrival.copy()
commonJson.update(jsonResponseObjDeparture)

# arrivels

for el in g.doc.select('//*[@id="arrival"]/table/tbody/tr'):
    arrival = getDataFromDocumentVVO(el)
    IdxOfLastEl = len(arrivals) - 1
    if IdxOfLastEl >= 0:
        if arrival["city"] == arrivals[IdxOfLastEl]["city"] and arrival["scheduled"] == arrivals[IdxOfLastEl]["scheduled"]:
            if not arrivals[IdxOfLastEl].has_key("codeshares"):
                arrivals[IdxOfLastEl]["codeshares"] = []
            arrivals[IdxOfLastEl]["codeshares"].append(arrival["flightno"])
            continue
    arrivals.append(arrival)

# departures

for el in g.doc.select('//*[@id="departure"]/table/tbody/tr'):
    departure = getDataFromDocumentVVO(el)
    IdxOfLastEl = len(departures) - 1
    if IdxOfLastEl >= 0:
        if departure["city"] == departures[IdxOfLastEl]["city"] and departure["scheduled"] == departures[IdxOfLastEl][
            "scheduled"]:
            if not departures[IdxOfLastEl].has_key("codeshares"):
                departures[IdxOfLastEl]["codeshares"] = []
            departures[IdxOfLastEl]["codeshares"].append(departure["flightno"])
            continue
    departures.append(departure)

for arrival in arrivals:
    arrival.pop("city")
for departure in departures:
    departure.pop("city")

resultVVO = {}
resultVVO["airport_id"] = "VVO"
resultVVO["departures"] = departures
resultVVO["arrivals"] = arrivals

jsonResult = json.dumps(resultVVO)
#print jsonResult