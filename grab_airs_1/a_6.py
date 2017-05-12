# -*- coding: utf-8 -*-

from grab import Grab
import json
from datetime import datetime, timedelta

departures = []
arrivals = []
datePattern = "%Y-%m-%d %H:%M:%S"
dateParamsPattern = "%d.%m.%y"
nowTime = datetime.now()


def getGrabWithToken():
    g = Grab(connect_timeout=90, timeout=90)
    urlOSS = "http://www.airport.kg/"
    g.go(urlOSS)
    _token = g.doc.select('/html/head/meta[3]/@content').text()
    g.setup(headers={'X-CSRF-Token': _token, "X-Requested-With":"XMLHttpRequest"})
    return g

REGISTRACIYA_POSADKA = "регистрация_посадка"
ZADERSHAN = "задержан"
REGISTRACIYA_2 = "регистрация"
POSADKA_2 = "посадка"
PO_GOTOVNOSTI = "по готовности"
OTPRAVLEN_2 = "отправлен"
PRIZEMLILSYA = "приземлился"
PO_RASPISANIYU_2 = "по расписанию"

DELAYED = "delayed"
OUTGATE = "outgate"
BOARDING = "boarding"
CHECKIN = "checkin"
EXPECTED = "expected"
LANDED = "landed"
DEPARTED = "departed"
SCHEDULED = "scheduled"

def fixStatus(status):
    return {
        ZADERSHAN:DELAYED,
        REGISTRACIYA_2:CHECKIN,
        REGISTRACIYA_POSADKA:OUTGATE,
        POSADKA_2:BOARDING,
        PO_GOTOVNOSTI:OUTGATE,
        PRIZEMLILSYA : LANDED,
        OTPRAVLEN_2 : DEPARTED,
        PO_RASPISANIYU_2 : SCHEDULED
    }.get(status, "")

def getDataFromDocumentOSS(el, isDeparture=False):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""
    codeShares = []
    gate = ""
    day = ""

    if isDeparture:
        try:
            flightnoSrc = str(el.select('.//div[1]/img/@src').text())
            idxOfAviaSlash = flightnoSrc.find("avia")
            flightno = flightnoSrc[idxOfAviaSlash + 5:]
            flightno = str.upper(flightno)
        except:
            flightno = ""
    else:
        try:
            flightno = str(el.select('.//div[2]').text())
            flightno = str.upper(flightno)
        except:
            flightno = ""

    if not isDeparture:
        try:
            rawScheduled = str(el.select('.//div[4]').text()) + " " + str(el.select('.//div[5]').text())
            rawDateTime = datetime.strptime(rawScheduled, '%d.%m.%y %H.%M')
            scheduled = rawDateTime.strftime(datePattern)
        except:
            scheduled = ""

        try:
            rawActual = str(el.select('.//div[7]').text()) + " " + str(el.select('.//div[8]').text())
            rawDateTime = datetime.strptime(rawActual, '%d.%m.%y %H.%M')
            actual = rawDateTime.strftime(datePattern)
        except:
            actual = ""

        try:
            rawStatus = el.select('.//div[6]').text()
            rawStatus = rawStatus.encode("utf-8")
            status = fixStatus(rawStatus)
        except:
            rawStatus = ""
            status = ""

        if status == "":
            status = SCHEDULED
    else:
        try:
            rawScheduled = str(el.select('.//div[3]').text()) + " " + str(el.select('.//div[4]').text())
            rawDateTime = datetime.strptime(rawScheduled, '%d.%m.%y %H.%M')
            scheduled = rawDateTime.strftime(datePattern)
        except:
            scheduled = ""

        try:
            rawActual = str(el.select('.//div[6]').text()) + " " + str(el.select('.//div[7]').text())
            rawDateTime = datetime.strptime(rawActual, '%d.%m.%y %H.%M')
            actual = rawDateTime.strftime(datePattern)
        except:
            actual = ""

        try:
            rawStatus = el.select('.//div[5]').text()
            rawStatus = rawStatus.encode("utf-8")
            status = fixStatus(rawStatus)
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
    if actual != "":
        result["actual"] = actual
    return result


# ARRIVE

urlOSSArrive = "http://www.airport.kg/changeArrTable"

#four hours ago
timeFourHourAgo = nowTime - timedelta(hours=4)
if timeFourHourAgo.day != nowTime.day:

    formatedYesterdayTime = timeFourHourAgo.strftime(dateParamsPattern)
    todayArrivalsParams = {
        "date": formatedYesterdayTime,
        "full": 1,
        "prefix": "osh"
    }

    g = getGrabWithToken()
    resp = g.go(urlOSSArrive, post=todayArrivalsParams)

    for el in g.doc.select("//div[contains(@class, 'm-row')]"):
        arrival = getDataFromDocumentOSS(el)
        arrivals.append(arrival)

#now
formatedNowTime = nowTime.strftime(dateParamsPattern)
todayArrivalsParams  = {
    "date": formatedNowTime,
    "full": 1,
    "prefix":"osh"
}
g = getGrabWithToken()
resp = g.go(urlOSSArrive, post=todayArrivalsParams)

for el in g.doc.select("//div[contains(@class, 'm-row')]"):
    arrival = getDataFromDocumentOSS(el)
    arrivals.append(arrival)

# tommorow
timeTommorow = nowTime + timedelta(days=1)
formatedTommorowTime = timeTommorow.strftime(dateParamsPattern)
todayArrivalsParams = {
    "date": formatedTommorowTime,
    "full": 1,
    "prefix": "osh"
}
g = getGrabWithToken()
resp = g.go(urlOSSArrive, post=todayArrivalsParams)

for el in g.doc.select("//div[contains(@class, 'm-row')]"):
    arrival = getDataFromDocumentOSS(el)
    arrivals.append(arrival)


# DEPARTURE
urlOSSDeparture = "http://www.airport.kg/changeDepTable"

#four hours ago
timeFourHourAgo = nowTime - timedelta(hours=4)
if timeFourHourAgo.day != nowTime.day:

    formatedYesterdayTime = timeFourHourAgo.strftime(dateParamsPattern)
    todayArrivalsParams = {
        "date": formatedYesterdayTime,
        "full": 1,
        "prefix": "osh"
    }

    g = getGrabWithToken()
    resp = g.go(urlOSSDeparture, post=todayArrivalsParams)

    for el in g.doc.select("//div[contains(@class, 'm-row')]"):
        departure = getDataFromDocumentOSS(el, True)
        departures.append(departure)


#now
formatedNowTime = nowTime.strftime(dateParamsPattern)
todayArrivalsParams  = {
    "date": formatedNowTime,
    "full": 1,
    "prefix":"osh"
}

g = getGrabWithToken()
resp = g.go(urlOSSDeparture, post=todayArrivalsParams)

for el in g.doc.select("//div[contains(@class, 'm-row')]"):
    departure = getDataFromDocumentOSS(el, True)
    departures.append(departure)

# tommorow
timeTommorow = nowTime + timedelta(days=1)
formatedTommorowTime = timeTommorow.strftime(dateParamsPattern)
todayArrivalsParams = {
    "date": formatedTommorowTime,
    "full": 1,
    "prefix":"osh"
}

g = getGrabWithToken()
resp = g.go(urlOSSDeparture, post=todayArrivalsParams)

for el in g.doc.select("//div[contains(@class, 'm-row')]"):
    departure = getDataFromDocumentOSS(el, True)
    departures.append(departure)

resultOSS = {}
resultOSS["airport_id"] = "OSS"
resultOSS["departures"] = departures
resultOSS["arrivals"] = arrivals

jsonResult = json.dumps(resultOSS)
#print jsonResult