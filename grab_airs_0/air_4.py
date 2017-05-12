# -*- coding: utf-8 -*-

from grab import Grab
import time
import json
import re
from datetime import datetime, timedelta

g = Grab(connect_timeout=50, timeout=50)

DEPARTED = "departed"
SCHEDULED = "scheduled"
CANCELLED = "cancelled"
EXPECTED = "expected"
LANDED = "landed"
DELAYED = "delayed"

EN_STATUS = "en vol"
PR_STATUS = "pr"
ARRIV_STATUS = "arriv"
ANNUL_STATUS = "annul"

def fixStatus(status):
    return {
        PR_STATUS: SCHEDULED,
        ANNUL_STATUS: CANCELLED,
        EN_STATUS: EXPECTED,
        ARRIV_STATUS: LANDED,
    }.get(status, "")


def getFullDate(hourMinute, justToday=False):
    datePattern = "%Y-%m-%d %H:%M:%S"
    nowTime = datetime.now()
    correctDate = nowTime

    h = int(hourMinute[:2])
    m = int(hourMinute[3:])

    if justToday == False:
        if h < nowTime.hour or (h == nowTime.hour and m < nowTime.minute):
            correctDate += timedelta(days=1)

    notFormatedTime = correctDate.replace(hour=h, minute=m, second=0)

    formatedTime = notFormatedTime.strftime(datePattern)
    return formatedTime

departures = []
arrivals = []

currentTimestamp = int(round(time.time() * 1000))
urlALGArrive = "http://www.elmatar.com/vols-arrivee/?listeVolsArrive=1&aeroport=DAAG&t=" + str(currentTimestamp)
resp = g.go(urlALGArrive)

for el in g.doc.select('//table/tbody/tr'):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    summaryFullTime = ""
    rawStatus = ""
    numGate = -1

    try:
        flightno = el.select('.//td[1]').text()
        if len(flightno) > 10:
            continue
    except:
        flightno = ""

    try:
        scheduledShortTime = el.select('.//td[4]').text()
        if scheduledShortTime != "-":
            scheduled = getFullDate(scheduledShortTime, True)
    except:
        scheduled = ""

    try:
        actualShortTime = el.select('.//td[5]').text()
        if actualShortTime != "-":
            actualShortTime = actualShortTime.replace("~", "")
            actualShortTime = actualShortTime.strip()
            actual = getFullDate(actualShortTime, True)
    except:
        actual = ""

    try:
        rawStatus = el.select('.//td[6]/span').text()
        m = re.search("([a-zA-Z\sàâäèéêëîïôœùûüÿçÀÂÄÈÉÊËÎÏÔŒÙÛÜŸÇ]*)", rawStatus)
        if m:
            matchedStatus = str.lower(str(m.groups()[0]))
            status = fixStatus(matchedStatus)
            if matchedStatus == EN_STATUS or matchedStatus == PR_STATUS:
                estimated = actual
                actual = ""
    except:
        status = ""

    if len(status) <= 0:
        status = SCHEDULED

    arrival = {
        "flightno": flightno,
        "scheduled": scheduled,
        "status": status,
        "raw_status": rawStatus
    }

    if estimated != "":
        arrival["estimated"] = estimated
    if actual != "":
        arrival["actual"] = actual

    jsonArrival = json.dumps(arrival)
    arrivals.append(jsonArrival)


urlALGDeparture = "http://www.elmatar.com/vols-depart/?listeVolsDepart=1&aeroport=DAAG&t=" + str(currentTimestamp)
resp = g.go(urlALGDeparture)

for el in g.doc.select('//table/tbody/tr'):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    summaryFullTime = ""
    rawStatus = ""
    numGate = -1

    try:
        flightno = el.select('.//td[1]').text()
        if len(flightno) > 10:
            continue
    except:
        flightno = ""

    try:
        scheduledShortTime = el.select('.//td[4]').text()
        if scheduledShortTime != "-":
            scheduled = getFullDate(scheduledShortTime, True)
    except:
        scheduled = ""

    try:
        actualShortTime = el.select('.//td[5]').text()
        if actualShortTime != "-":
            actualShortTime = actualShortTime.replace("~", "")
            actualShortTime = actualShortTime.strip()
            actual = getFullDate(actualShortTime, True)
    except:
        actual = ""

    try:
        rawStatus = el.select('.//td[6]/span').text()
        m = re.search("([a-zA-Z\sàâäèéêëîïôœùûüÿçÀÂÄÈÉÊËÎÏÔŒÙÛÜŸÇ]*)", rawStatus)
        if m:
            matchedStatus = str.lower(str(m.groups()[0]))
            matchedStatus = matchedStatus.strip()
            if matchedStatus == PR_STATUS:
                status = SCHEDULED
                if actual != "" and scheduled != "":
                    scheduledDateTime = datetime.strptime(scheduled, '%Y-%m-%d %H:%M:%S')
                    actualDateTime = datetime.strptime(actual, '%Y-%m-%d %H:%M:%S')
                    if actualDateTime > scheduledDateTime:
                        status = DELAYED
                        estimated = actual
                        actual = ""
            if matchedStatus == ANNUL_STATUS:
                status = CANCELLED
            elif matchedStatus == EN_STATUS:

                status = DEPARTED
            elif matchedStatus == ARRIV_STATUS:
                status = DEPARTED
    except:
        status = ""

    if len(status) <= 0:
        status = SCHEDULED

    departure = {
        "flightno": flightno,
        "scheduled": scheduled,
        "status": status,
        "raw_status": rawStatus
    }

    if estimated != "":
        departure["estimated"] = estimated
    if actual != "":
        departure["actual"] = actual

    jsonDeparture = json.dumps(departure)
    departures.append(jsonDeparture)

resultALG = {}
resultALG["airport_id"] = "ALG"
resultALG["departures"] = departures
resultALG["arrivals"] = arrivals

jsonResultALG = json.dumps(resultALG)
print jsonResultALG
