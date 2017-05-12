# -*- coding: utf-8 -*-

from grab import Grab
import time
import json
from datetime import datetime, timedelta
from lxml.html import fromstring
import re

g = Grab(connect_timeout=90, timeout=90)
datePattern = "%Y-%m-%d %H:%M:%S"
nowTime = datetime.now()
departures = []
arrivals = []

PRILETEL_S_ZADERSHKOY = "Прилетел с задержкой"
PRILETEL = "Прилетел"
OSHIDAETSA = "Ожидается"
VILETEL = "Вылетел"
OTMENEN = "Отменен"

POSADKA_ZAVERSHINA = "Посадка завершена"
ZADERSHIVAETSA = "Задерживается"
PO_RASPISANIYU_3 = "По расписанию"

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
        PRILETEL_S_ZADERSHKOY:LANDED,
        OSHIDAETSA:SCHEDULED,
        PRILETEL:LANDED,

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

def getFullDate(hourMinute, day):
    datePattern = "%Y-%m-%d %H:%M:%S"
    nowTime = datetime.now()
    correctDate = nowTime

    h = int(hourMinute[:2])
    m = int(hourMinute[3:])

    notFormatedTime = correctDate.replace(day=day, hour=h, minute=m, second=0)

    formatedTime = notFormatedTime.strftime(datePattern)
    return formatedTime

def getDataFromDocumentKHV(el):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""

    try:
        rawStatus = el.select('.//td[6]').text()
        rawStatus = rawStatus.encode("utf-8")
        if rawStatus.find(" ") > 0:
            status = fixStatus(rawStatus[:rawStatus.find(" ")])
        else:
            status = fixStatus(rawStatus)
    except:
        rawStatus = ""

    if status == "":
        status = SCHEDULED

    try:
        flightno = el.select('.//td[2]').text()
        flightno = flightno.encode("utf-8")

        try:
            otherInformation = el.select('.//td[2]/span/@onclick').text()
            match = re.search(".*(<table .*?><\/table>).*", otherInformation)
            if match:
                table = match.groups()[0]
                dom = fromstring(table)

                try:
                    scheduledString = dom.xpath('//table/tr[2]/td[2]')[0].text_content() + " " + str(nowTime.year)
                    scheduledDateTime = datetime.strptime(scheduledString, "%d %b %H:%M %Y")
                    scheduled = scheduledDateTime.strftime(datePattern)
                except:
                    scheduled = ""
                try:
                    actualString = dom.xpath('//table/tr[3]/td[2]')[0].text_content() + " " + str(nowTime.year)
                    actualDateTime = datetime.strptime(actualString, "%d %b %H:%M %Y")
                    actual = actualDateTime.strftime(datePattern)
                    if status == DELAYED:
                        estimated = actual
                        actual = ""
                except:
                    actual = ""
        except:
            scheduled = ""
            actual = ""
    except:
        flightno = ""
        scheduled = ""
        actual = ""

    result = {
        "flightno": flightno,
        "scheduled": scheduled,
        "status": status,
        "raw_status": rawStatus
    }
    if actual != "":
        result["actual"] = actual
    if estimated != "":
        result["estimated"] = estimated
    return result


# Yesterday
yesterdayTime = nowTime - timedelta(days=1)

yesterdayUrl = "http://airkhv.ru/components/com_tablo/ajax-worker.php?kolFlights=0&dateVal=-1"
yesterdayTimeStamp = int(time.mktime(yesterdayTime.timetuple()) + yesterdayTime.microsecond / 1E6)

currentTimeStamp = int(round(time.time()))
resp = g.go(yesterdayUrl, post={"rndval":yesterdayTimeStamp})

# ARRIVED
i = 0
for el in g.doc.select('//inflight[1]/div/div/table/tbody/tr'):
    i += 1
    if i == 1:
        continue
    flightno = el.select('.//td[2]').text().encode("utf-8")
    if flightno == "Номеррейса":
        break
    arrival = getDataFromDocumentKHV(el)
    arrivals.append(arrival)

# DEPARTED
i = 0
for el in g.doc.select('//outflight[1]/div/div/table/tbody/tr'):
    i += 1
    if i == 1:
        continue
    flightno = el.select('.//td[2]').text().encode("utf-8")
    if flightno == "Номеррейса":
        break
    departure = getDataFromDocumentKHV(el)
    departures.append(departure)

# Today
url = "http://airkhv.ru/components/com_tablo/ajax-worker.php?kolFlights=0&dateVal=0"

currentTimeStamp = int(round(time.time()))
resp = g.go(url, post={"rndval":currentTimeStamp})

# ARRIVED
i = 0
for el in g.doc.select('//inflight[1]/div/div/table/tbody/tr'):
    i += 1
    if i == 1:
        continue
    flightno = el.select('.//td[2]').text().encode("utf-8")
    if flightno == "Номеррейса":
        break
    arrival = getDataFromDocumentKHV(el)
    arrivals.append(arrival)

# DEPARTED
i = 0
for el in g.doc.select('//outflight[1]/div/div/table/tbody/tr'):
    i += 1
    if i == 1:
        continue
    flightno = el.select('.//td[2]').text().encode("utf-8")
    if flightno == "Номеррейса":
        break
    departure = getDataFromDocumentKHV(el)
    departures.append(departure)


# Tomorrow
tomorrowTime = nowTime - timedelta(days=1)

tomorrowUrl = "http://airkhv.ru/components/com_tablo/ajax-worker.php?kolFlights=0&dateVal=1"
tomorrowTimeStamp = int(time.mktime(tomorrowTime.timetuple()) + tomorrowTime.microsecond / 1E6)

currentTimeStamp = int(round(time.time()))
resp = g.go(tomorrowUrl, post={"rndval":tomorrowTimeStamp})

# ARRIVED
i = 0
for el in g.doc.select('//inflight[1]/div/div/table/tbody/tr'):
    i += 1
    if i == 1:
        continue
    flightno = el.select('.//td[2]').text().encode("utf-8")
    if flightno == "Номеррейса":
        break
    arrival = getDataFromDocumentKHV(el)
    arrivals.append(arrival)

# DEPARTED
i = 0
for el in g.doc.select('//outflight[1]/div/div/table/tbody/tr'):
    i += 1
    if i == 1:
        continue
    flightno = el.select('.//td[2]').text().encode("utf-8")
    if flightno == "Номеррейса":
        break
    departure = getDataFromDocumentKHV(el)
    departures.append(departure)


resultKHV = {}
resultKHV["airport_id"] = "KHV"
resultKHV["departures"] = departures
resultKHV["arrivals"] = arrivals

jsonResult = json.dumps(resultKHV)
#print jsonResult
