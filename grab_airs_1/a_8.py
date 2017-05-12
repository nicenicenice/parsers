# -*- coding: utf-8 -*-

from grab import Grab
import json
from datetime import datetime, timedelta
import re

g = Grab(connect_timeout=90, timeout=90)
g.setup(headers={"X-Requested-With":"XMLHttpRequest"})


OTMENEN = "Отменён"
POSADKA_ZAVERSHINA = "Посадка завершена"
ZADERSHIVAETSA = "Задерживается"
PO_RASPISANIYU_3 = "По расписанию"
VILETEL = "Вылетел"
REYS_PRIBIL = "Рейс прибыл"
V_POLETE_3 = "В полете"
POSADKA = "Посадка"
REGISTRACIYA = "Регистрация"

SCHEDULED = "scheduled"
DELAYED = "delayed"
CANCELLED = "cancelled"
CHECKIN = "checkin"
BOARDING = "boarding"
OUTGATE = "outgate"
DEPARTED = "departed"
EXPECTED = "expected"
LANDED = "landed"

def fixStatus(status):
    return {
        OTMENEN:CANCELLED,
        REGISTRACIYA:CHECKIN,
        V_POLETE_3:EXPECTED,
        REYS_PRIBIL : LANDED,
        VILETEL : DEPARTED,
        POSADKA_ZAVERSHINA:OUTGATE,
        PO_RASPISANIYU_3 : SCHEDULED,
        ZADERSHIVAETSA:DELAYED,
        POSADKA:BOARDING
    }.get(status, "")

datePattern = "%Y-%m-%d %H:%M:%S"
nowTime = datetime.now()
departures = []
arrivals = []

def getFormatedCheckinDesks(checkinStr):
    if checkinStr.find(",") > 0:
        arDesks = checkinStr.split(",")
        return arDesks[0] + " - " + arDesks[len(arDesks) - 1]
    else:
        return checkinStr

def getSecondPardOfData(data):
    indexOfColon = data.find(":")
    return data[indexOfColon + 2:]

def getDataFromDocumentPEE(el, isDeparture=False):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""
    terminal = ""
    gate = ""
    check_in_desks = ""
    luggage = ""

    try:
        rawFlightno = el.select('.//div[1]/span[1]').text()
        flightno = rawFlightno.encode("utf-8")
    except:
        flightno = ""

    try:
        rawScheduled = el.select('.//div[2]/ul[1]/li[2]').text()
        rawScheduled = getSecondPardOfData(rawScheduled) + "." + str(nowTime.year)
        rawDateTime = datetime.strptime(rawScheduled, '%H:%M, %d.%m.%Y')
        scheduled = rawDateTime.strftime(datePattern)
    except:
        scheduled = ""
    try:
        rawEstimated = getSecondPardOfData(el.select('.//div[2]/ul[1]/li[3]').text())
        rawEstimated = rawEstimated + "." + str(nowTime.year)
        rawDateTime = datetime.strptime(rawEstimated, '%H:%M, %d.%m.%Y')
        estimated = rawDateTime.strftime(datePattern)
    except:
        estimated = ""

    try:
        terminal = getSecondPardOfData(el.select('.//div[2]/ul[1]/li[4]').text())
    except:
        terminal = ""

    if not isDeparture:
        try:
            luggage = getSecondPardOfData(el.select('.//div[2]/ul[2]/li[3]').text())
        except:
            luggage = ""

    if isDeparture:
        try:
            rawCheckInDesks = getSecondPardOfData(el.select('.//div[2]/ul[2]/li[3]').text())
            check_in_desks = getFormatedCheckinDesks(rawCheckInDesks)
        except:
            check_in_desks = ""

    try:
        gate = getSecondPardOfData(el.select('.//div[2]/ul[3]/li[3]').text())
    except:
        gate = ""

    try:
        rawStatus = el.select('.//div[1]/span[6]').text()
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
    if luggage != "":
        result["luggage"] = luggage
    if check_in_desks != "":
        result["check_in_desks"] = check_in_desks
    if estimated != "":
        result["estimated"] = estimated
    if gate != "":
        result["gate"] = gate
    if terminal != "":
        result["terminal"] = terminal
    return result

#if rel is departure then div with arrive article will has unvisible attr
urlPEE = "http://www.aviaperm.ru/ajax/ttable.php"
# ARRIVE

#four hours ago
timeFourHourAgo = nowTime - timedelta(hours=4)
if timeFourHourAgo.day != nowTime.day:

    yesterdayParams = {
        "day": "yesterday",
        "items_count": 0,
        "rel": "departure"
    }
    resp = g.go(urlPEE, post=yesterdayParams)

    for el in g.doc.select("//section/div/div/div[contains(@class, 'unvisible')]/div/div/article"):
        arrival = getDataFromDocumentPEE(el)
        arrivals.append(arrival)
#today
todayParams = {
    "day": "today",
    "items_count": 0,
    "rel": "departure"
}
resp = g.go(urlPEE, post=todayParams)

for el in g.doc.select("//section/div/div/div[contains(@class, 'unvisible')]/div/div/article"):
    arrival = getDataFromDocumentPEE(el)
    arrivals.append(arrival)

# tomorrow
tommorowParams = {
    "day": "tomorrow",
    "items_count": 0,
    "rel": "departure"
}
resp = g.go(urlPEE, post=tommorowParams)

for el in g.doc.select("//section/div/div/div[contains(@class, 'unvisible')]/div/div/article"):
    arrival = getDataFromDocumentPEE(el)
    arrivals.append(arrival)



# DEPARTURE

#four hours ago
timeFourHourAgo = nowTime - timedelta(hours=4)
if timeFourHourAgo.day != nowTime.day:

    yesterdayParams = {
        "day": "yesterday",
        "items_count": 0,
        "rel": "departure"
    }

    resp = g.go(urlPEE, post=yesterdayParams)

    for el in g.doc.select("//section/div/div/div[not(contains(@class, 'unvisible'))]/div/div/article"):
        departure = getDataFromDocumentPEE(el, True)
        departures.append(departure)
#today
todayParams = {
    "day": "today",
    "items_count": 0,
    "rel": "departure"
}
resp = g.go(urlPEE, post=todayParams)

for el in g.doc.select("//section/div/div/div[not(contains(@class, 'unvisible'))]/div/div/article"):
    departure = getDataFromDocumentPEE(el, True)
    departures.append(departure)

# tomorrow
tommorowParams = {
    "day": "tomorrow",
    "items_count": 0,
    "rel": "departure"
}
resp = g.go(urlPEE, post=tommorowParams)

for el in g.doc.select("//section/div/div/div[not(contains(@class, 'unvisible'))]/div/div/article"):
    departure = getDataFromDocumentPEE(el, True)
    departures.append(departure)

resultPEE = {}
resultPEE["airport_id"] = "PEE"
resultPEE["departures"] = departures
resultPEE["arrivals"] = arrivals

jsonResult = json.dumps(resultPEE)
#print jsonResult
