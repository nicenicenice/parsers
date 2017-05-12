# -*- coding: utf-8 -*-

from grab import Grab
import json
from datetime import datetime

g = Grab(connect_timeout=50, timeout=50)

urlABA = "http://abakan.aero/"
resp = g.go(urlABA)

PRIBIL = "Прибыл"
OTPRAVLEN = "Отправлен"
PO_RASPISANIYU = "По расписанию"
LANDED = "landed"
DEPARTED = "departed"
SCHEDULED = "scheduled"

departures = []
arrivals = []

def fixStatus(status):
    return {
        PRIBIL : LANDED,
        OTPRAVLEN : DEPARTED,
        PO_RASPISANIYU : SCHEDULED
    }.get(status, "")

def getDataFromDocumentABA(el):
    scheduled = ""
    flightno = ""
    status = ""
    rawStatus = ""

    try:
        firstPartOfData = el.select('.//td[2]/p[1]').text()

        secondPartOfData = el.select('.//td[2]/p[2]').text()
        secondPartOfData = secondPartOfData.replace("*", "")
        secondPartOfData = secondPartOfData.replace(".", ":")

        compesedDate = firstPartOfData + " " + secondPartOfData + ":00"

        scheduled = datetime.strptime(compesedDate, '%d.%m.%Y %H:%M:%S')
        datePattern = "%Y-%m-%d %H:%M:%S"
        scheduled = scheduled.strftime(datePattern)
    except:
        scheduled = ""
    try:
        flightno = el.select('.//td[1]/p[1]').text()
    except:
        flightno = ""

    try:
        rawStatus = el.select('.//td[3]/span').text()
        rawStatus = rawStatus.encode("utf-8")
        status = fixStatus(rawStatus)
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
    return result


for el in g.doc.select('//*[@id="arr"]/table/tr'):
    arrival = getDataFromDocumentABA(el)
    arrivals.append(arrival)


for el in g.doc.select('//*[@id="dep"]/table/tr'):
    departure = getDataFromDocumentABA(el)
    departures.append(departure)

resultABA = {}
resultABA["airport_id"] = "ABA"
resultABA["departures"] = departures
resultABA["arrivals"] = arrivals

jsonResultABA = json.dumps(resultABA)
print jsonResultABA