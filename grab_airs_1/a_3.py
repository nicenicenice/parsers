# -*- coding: utf-8 -*-

from grab import Grab
import json
from datetime import datetime, timedelta
import re

g = Grab(connect_timeout=90, timeout=90)

CHECKIN = "checkin"
_REGISTRACIYA = "РЕГИСТРАЦИЯ"
_POSADKA = "ПОСАДКА"
_V_POLETE = "В ПОЛЕТЕ"
EXPECTED = "expected"
_PRIBIL = "ПРИБЫЛ"
_VILETEL = "ВЫЛЕТЕЛ"
_PO_RASPISANIYU = "ПО РАСПИСАНИЮ"
LANDED = "landed"
DEPARTED = "departed"
SCHEDULED = "scheduled"

departures = []
arrivals = []
datePattern = "%Y-%m-%d %H:%M:%S"
nowTime = datetime.now()

def fixStatus(status):
    return {
        _REGISTRACIYA:CHECKIN,
        _V_POLETE:EXPECTED,
        _PRIBIL : LANDED,
        _VILETEL : DEPARTED,
        _PO_RASPISANIYU : SCHEDULED
    }.get(status, "")

def getFullDate(hourMinute, day):
    datePattern = "%Y-%m-%d %H:%M:%S"
    nowTime = datetime.now()
    correctDate = nowTime

    h = int(hourMinute[:2])
    m = int(hourMinute[3:])

    notFormatedTime = correctDate.replace(day=day, hour=h, minute=m, second=0)

    formatedTime = notFormatedTime.strftime(datePattern)
    return formatedTime

def getDataFromDocumentNUX(el, day):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""
    codeShares = []
    gate = ""

    try:
        arFlights = []
        flightnoString = el.select('.//td[1]').text()
        flightnoString = flightnoString.encode("utf-8")

        arRawFlightno = re.split("([A-ZА-Я]+ [\d]+)", flightnoString)
        for flight in arRawFlightno:
            if flight != "":
                arFlights.append(flight)

        flightno = arFlights[0]
        if len(arFlights) > 1:
            for i in range(1, len(arFlights)):
                codeShares.append(arFlights[i])
    except:
        flightno = ""

    try:
        rawScheduled = str(el.select('.//td[3]').text())
        fullRawScheduled = rawScheduled + "/" + str(nowTime.year)
        rawDateTime = datetime.strptime(fullRawScheduled, '%H:%M %d/%m/%Y')

        scheduled = rawDateTime.strftime(datePattern)
    except:
        scheduled = ""

    try:
        rawEstimated = str(el.select('.//td[4]').text())

        fullRawEstimated = rawEstimated + "/" + str(nowTime.year)
        rawDateTime = datetime.strptime(fullRawEstimated, '%H:%M %d/%m/%Y')
        estimated = rawDateTime.strftime(datePattern)
    except:
        estimated = ""

    try:
        rawStatus = el.select('.//td[6]').text()
        if rawStatus != "-":
            rawStatus = rawStatus.encode("utf-8")
            rawStatus = str.lower(str(rawStatus))

            m = re.search("([а-яА-Я]+( [а-яА-Я]+)?)?\s?(\d{2}[\:]\d{2})?", rawStatus)
            if m:
                rawStatus = str.lower(m.groups()[0])
                status = fixStatus(rawStatus)
                if m.groups()[2] is not None:
                    rawActual = str.lower(m.groups()[2])
                    actual = getFullDate(rawActual, rawDateTime.day)
    except:
        rawStatus = ""
        status = ""
        actual = ""

    if status == "":
        status = SCHEDULED

    result = {
        "flightno": flightno,
        "scheduled": scheduled,
        "status": status,
        "raw_status": rawStatus
    }
    if estimated != "":
        result["estimated"] = estimated
    if actual != "":
        result["actual"] = actual
    if len(codeShares) > 0:
        result["codeshares"] = codeShares
    return result


urlNUX = "http://nux.aero/index.php"
resp = g.go(urlNUX)

i = 0
for el in g.doc.select('//*[@id="gk-tabs-168"]/div/div/div[2]//table/tr'):
    i += 1
    if i == 1:
        continue
    arrival = getDataFromDocumentNUX(el, nowTime.day)
    arrivals.append(arrival)


i = 0
for el in g.doc.select('//*[@id="gk-tabs-168"]/div/div/div[1]//table/tr'):
    i += 1
    if i == 1:
        continue
    departure = getDataFromDocumentNUX(el, nowTime.day)
    departures.append(departure)

resultNUX = {}
resultNUX["airport_id"] = "NUX"
resultNUX["departures"] = departures
resultNUX["arrivals"] = arrivals

jsonResult = json.dumps(resultNUX)
#print jsonResult


