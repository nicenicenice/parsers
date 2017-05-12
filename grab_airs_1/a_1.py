# -*- coding: utf-8 -*-

from grab import Grab
import json
from datetime import datetime, timedelta

g = Grab(connect_timeout=90, timeout=90)

CHECKIN = "checkin"
REGISTRACIYA = "Регистрация"
POSADKA = "Посадка"
POSADKA_ZAVERSHENA = "Пос.Завершена"
V_POLETE = "В Полете"
EXPECTED = "expected"
PRIBIL = "Прибыл"
OTPRAVLEN = "Отправлен"
PO_RASPISANIYU = "По Расписанию"
LANDED = "landed"
DEPARTED = "departed"
SCHEDULED = "scheduled"
OUTGATE = "outgate"
BOARDING = "boarding"

departures = []
arrivals = []

def getFullDate(hourMinute, day):
    datePattern = "%Y-%m-%d %H:%M:%S"
    nowTime = datetime.now()
    correctDate = nowTime

    h = int(hourMinute[:2])
    m = int(hourMinute[3:])

    notFormatedTime = correctDate.replace(day=day, hour=h, minute=m, second=0)

    formatedTime = notFormatedTime.strftime(datePattern)
    return formatedTime

def fixStatus(status):
    return {
        REGISTRACIYA:CHECKIN,
        V_POLETE:EXPECTED,
        POSADKA:BOARDING,
        POSADKA_ZAVERSHENA:OUTGATE,
        PRIBIL : LANDED,
        OTPRAVLEN : DEPARTED,
        PO_RASPISANIYU : SCHEDULED
    }.get(status, "")

def getDataFromDocumentMRV(el, day, isTommorow=False):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""

    try:
        flightno = el.select('.//td[3]').text()
    except:
        flightno = ""
    try:
        scheduled = el.select('.//td[4]').text()
        scheduled = getFullDate(scheduled, day)
    except:
        scheduled = ""

    if isTommorow == False:
        try:
            actual = str(el.select('.//td[5]').text())
            if actual != "-":
                actual = getFullDate(actual, day)
            else:
                actual = ""
        except:
            actual = ""
        try:
            rawStatus = el.select('.//td[7]/span').text()
            rawStatus = rawStatus.encode("utf-8")
            status = fixStatus(rawStatus)
        except:
            rawStatus = ""
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


nowTime = datetime.now()
urlMRV = "http://www.mvairport.ru/ctrl/schedule/ajax_schedule.php"

#arrival

#four hours ago
timeFourHourAgo = nowTime - timedelta(hours=4)
if timeFourHourAgo.day != nowTime.day:
    fourHourAgoDayArrivalsParams = {
        "day": str(timeFourHourAgo.day) + "." + str(timeFourHourAgo.month) + "." + str(timeFourHourAgo.year),
        "direct": "1"
    }
    resp = g.go(urlMRV, post=fourHourAgoDayArrivalsParams)

    for el in g.doc.select('//tbody/tr'):
        arrival = getDataFromDocumentMRV(el, timeFourHourAgo.day)
        arrivals.append(arrival)
        
#now
todayArrivalsParams  = {
    "day" : str(nowTime.day) + "." + str(nowTime.month) + "." + str(nowTime.year),
    "direct":"1"
}

resp = g.go(urlMRV, post=todayArrivalsParams)

for el in g.doc.select('//tbody/tr'):
    arrival = getDataFromDocumentMRV(el, nowTime.day)
    arrivals.append(arrival)

#tommorow
tommorowAgo = nowTime + timedelta(days=1)
tommorowArrivalsParams = {
        "day": str(tommorowAgo.day) + "." + str(tommorowAgo.month) + "." + str(tommorowAgo.year),
        "direct": "1"
    }
resp = g.go(urlMRV, post=tommorowArrivalsParams)

for el in g.doc.select('//tbody/tr'):
    arrival = getDataFromDocumentMRV(el, tommorowAgo.day, True)
    arrivals.append(arrival)





#departure

#four hours ago
timeFourHourAgo = nowTime - timedelta(hours=4)
if timeFourHourAgo.day != nowTime.day:
    fourHourAgoDayArrivalsParams = {
        "day": str(timeFourHourAgo.day) + "." + str(timeFourHourAgo.month) + "." + str(timeFourHourAgo.year),
        "direct": "2"
    }
    resp = g.go(urlMRV, post=fourHourAgoDayArrivalsParams)

    for el in g.doc.select('//tbody/tr'):
        departure = getDataFromDocumentMRV(el, timeFourHourAgo.day)
        departures.append(departure)

#now
todayDepartureParams  = {
    "day" : str(nowTime.day) + "." + str(nowTime.month) + "." + str(nowTime.year),
    "direct":"2"
}

resp = g.go(urlMRV, post=todayDepartureParams)

for el in g.doc.select('//tbody/tr'):
    departure = getDataFromDocumentMRV(el, nowTime.day)
    departures.append(departure)

#tommorow
tommorowAgo = nowTime + timedelta(days=1)
tommorowArrivalsParams = {
        "day": str(tommorowAgo.day) + "." + str(tommorowAgo.month) + "." + str(tommorowAgo.year),
        "direct": "2"
    }
resp = g.go(urlMRV, post=tommorowArrivalsParams)

for el in g.doc.select('//tbody/tr'):
    departure = getDataFromDocumentMRV(el, tommorowAgo.day, True)
    departures.append(departure)

resultMRV = {}
resultMRV["airport_id"] = "MRV"
resultMRV["departures"] = departures
resultMRV["arrivals"] = arrivals

jsonResult = json.dumps(resultMRV)
#print jsonResult






