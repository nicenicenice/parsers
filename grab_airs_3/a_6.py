# -*- coding: utf-8 -*-

from grab import Grab
import json
import time
import re
from datetime import datetime, timedelta

departures = []
arrivals = []
datePattern = "%Y-%m-%d %H:%M:%S"
dateParamsPattern = "%d.%m.%y"
nowTime = datetime.now()



#Отменён
#Произвёл посадку пассажиры р.5Н 118
#Произвёл посадку
#Вылетел в 16:02
#Ожидается в 16:05
#Отменён . Прибытие пассажиров р. 5Н1118 02.05.17г

#Регистрация. Стойка 2,6,7. Посадка-ВЫХОД 3 /Замена ВС на ЯК-42
#Регистрация. Стойка 2,5,6,7. Посадка-ВЫХОД 1


OTMENEN_ = "Отменён "
OTMENEN = "Отменён"
PROIZVEL = "Произвёл"
VILETEL = "Вылетел"
OSHIDAETSYA = "Ожидается"
REGISTRAZIYA = "Регистрация"
POSADKA = "Посадка"
OTPRAVLEN = "Отправлен"

DELAYED = "delayed"
OUTGATE = "outgate"
BOARDING = "boarding"
CHECKIN = "checkin"
EXPECTED = "expected"
LANDED = "landed"
DEPARTED = "departed"
SCHEDULED = "scheduled"
CANCELLED = "cancelled"

def fixStatus(status):
    return {
        OSHIDAETSYA:EXPECTED,
        OTMENEN:CANCELLED,
        OTMENEN_:CANCELLED,
        REGISTRAZIYA:CHECKIN,
        POSADKA:BOARDING,
        OTPRAVLEN:DEPARTED,
        PROIZVEL : LANDED
    }.get(status, "")

def getFullDate(hourMinute, scheduleDateTime):
    datePattern = "%Y-%m-%d %H:%M:%S"
    nowTime = datetime.now()
    correctDate = nowTime

    h = int(hourMinute[:2])
    m = int(hourMinute[3:])

    notFormatedTime = correctDate.replace(day=scheduleDateTime.day, hour=h, minute=m, second=0)

    if scheduleDateTime.hour > 20 and h < 5:
        notFormatedTime = notFormatedTime + timedelta(days=1)

    formatedTime = notFormatedTime.strftime(datePattern)
    return formatedTime

def getFormatedCheckinDesks(checkinStr):
    if checkinStr.find(",") > 0:
        arDesks = checkinStr.split(",")
        match = re.search("([a-zА-Я])", checkinStr)
        if not match:
            arDesks.sort(key=int)
        return arDesks[0] + " - " + arDesks[len(arDesks) - 1]
    else:
        return checkinStr

def getDataFromDocumentARH(el, dateTime, isDeparture=False):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""
    codeShares = []
    gate = ""
    arFlights = []
    check_in_desks = ""

    try:
        flightnoString = el.select('.//td[6]').text()

        flightnoString = flightnoString.encode("utf-8")
        arRawFlightno = re.split(" \/ ", flightnoString)

        for flight in arRawFlightno:
            if flight != "":
                arFlights.append(flight)

        flightno = arFlights[0]
        if len(arFlights) > 1:
            for i in range(1, len(arFlights)):
                codeShares.append(arFlights[i])
    except:
        flightno = ""
        codeShares = []
    try:
        if not isDeparture:
            rawScheduled = el.select('.//td[3]').text()
        else:
            rawScheduled = el.select('.//td[1]').text()
        h = int(rawScheduled[:2])
        m = int(rawScheduled[3:])

        dateTimeToCorrect = dateTime
        correctedScheduleDateTime = dateTimeToCorrect.replace(day=dateTime.day, hour=h, minute=m, second=0)

        scheduled = correctedScheduleDateTime.strftime(datePattern)
    except:
        scheduled = ""

    try:
        if not isDeparture:
            rawActual = el.select('.//td[4]').text()
        else:
            rawActual = el.select('.//td[2]').text()

        if rawActual != "-":
            actual = getFullDate(rawActual, correctedScheduleDateTime)
    except:
        actual = ""

    try:
        rawStatus = el.select('.//td[9]').text()
        rawStatus = rawStatus.encode("utf-8")

        if rawStatus.find("Задержан до") >= 0:
            newRawStatus = rawStatus[rawStatus.find("Задержан до")+22:rawStatus.find("Задержан до")+27]
            estimated = getFullDate(newRawStatus, correctedScheduleDateTime)
        if rawStatus.find("Перенос на") >= 0:
            newShortSchedule = rawStatus[rawStatus.find("Перенос на")+20:rawStatus.find("Перенос на")+28]
            newLongSchedule = rawStatus[rawStatus.find("Перенос на")+20:rawStatus.find("Перенос на")+34]
            try:
                newShortSchedule = str(newShortSchedule).strip() + " " + str(correctedScheduleDateTime.hour) + ":" + str(correctedScheduleDateTime.minute)
                newShortScheduleDateTime = datetime.strptime(newShortSchedule, "%d.%m.%y %H:%M")
                estimated = newShortScheduleDateTime.strftime(datePattern)
            except:
                newLongSchedule = str(newLongSchedule).strip()
                newLongScheduleDateTime = datetime.strptime(newLongSchedule, "%d.%m.%y %H:%M")
                estimated = newLongScheduleDateTime.strftime(datePattern)
        if rawStatus.find(" в ") >= 0:
            if rawStatus == OSHIDAETSYA:
                estimated = rawStatus[rawStatus.find(" в ") + 4:]
        if rawStatus.find("Стойка") >= 0:
            if rawStatus.find("Посадка") >= 0:
                check_in_desks = rawStatus[rawStatus.find("Стойка") + 13:rawStatus.find("Посадка") - 2]
                #check_in_desks = getFormatedCheckinDesks(check_in_desks)
                gate = str(rawStatus[rawStatus.find("ВЫХОД") + 11:rawStatus.find("ВЫХОД") + 13:]).strip()
        else:
            if rawStatus.find("Посадка") >= 0 and rawStatus.find("Посадка закончена") < 0:
                gate = str(rawStatus[rawStatus.find("ВЫХОД") + 11:rawStatus.find("ВЫХОД") + 13:]).strip()
        #match = re.search("([а-яёА-Я]+)[\.\s а-я]+([\d:]+)?(Стойка\s([\d,]+)\.\sПосадка\-ВЫХОД (\d).*?)?", rawStatus)

        if rawStatus.find("Перенос на") >= 0 or rawStatus.find("Задержан до") >= 0:
            status = DELAYED
        elif rawStatus.find("Произвёл посадку") >= 0:
            status = LANDED
        elif rawStatus.find("Посадка закончена") >= 0:
            status = OUTGATE
        elif rawStatus.find("Регистрация закончена") >= 0:
            status = BOARDING
        elif rawStatus.find("Отправлен пассажиры") >= 0:
            status = DEPARTED
        elif rawStatus.find(".") > 0:
            status = fixStatus(rawStatus[:rawStatus.find(".")])
        elif rawStatus.find(" ") > 0:
            status = fixStatus(rawStatus[:rawStatus.find(" ")])
        else:
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
    if len(codeShares) > 0:
        result["codeshares"] = codeShares
    if estimated != "":
        result["estimated"] = estimated
    if actual != "":
        result["actual"] = actual
    if gate != "":
        result["gate"] = gate
    if check_in_desks != "":
        result["check_in_desks"] = check_in_desks
    return result


def getTimeStampFromDateTime(datetime):
    return int(time.mktime(datetime.timetuple()) + datetime.microsecond / 1E6)

# ARRIVE
g = Grab(connect_timeout=90, timeout=90)

urlARH = "http://arhaero.ru/ajaxonlinetablo.php"



# Yesterday
yesterdayTime = nowTime - timedelta(days=1)
yesterdayTimeStamp = getTimeStampFromDateTime(yesterdayTime)
todayArrivalsParams = {
    "date":yesterdayTimeStamp,
    "type":"arrival"
}

resp = g.go(urlARH, post=todayArrivalsParams)

i = 0
for el in g.doc.select("//table/tbody/tr"):
    i += 1
    if i == 1:
        continue
    try:
        separator = el.select("./td/center").text()
        separator = separator.encode("utf-8")
        if separator == "Рейсы с окончательным статусом":
            continue
    except:
        try:
            headOfTable = el.select("./th").text()
            continue
        except:
            pass
    arrival = getDataFromDocumentARH(el, yesterdayTime)
    arrivals.append(arrival)

todayDepartureParams = {
    "date":yesterdayTimeStamp,
    "type":"departure"
}

resp = g.go(urlARH, post=todayDepartureParams)

for el in g.doc.select("//table/tbody/tr"):
    i += 1
    if i == 1:
        continue
    try:
        separator = el.select("./td/center").text()
        separator = separator.encode("utf-8")
        if separator == "Рейсы с окончательным статусом":
            continue
    except:
        try:
            headOfTable = el.select("./th").text()
            continue
        except:
            pass

    departure = getDataFromDocumentARH(el, yesterdayTime, True)
    departures.append(departure)


# Today
currentTimeStamp = getTimeStampFromDateTime(nowTime)
todayArrivalsParams = {
    "date":currentTimeStamp,
    "type":"arrival"
}

resp = g.go(urlARH, post=todayArrivalsParams)

i = 0
for el in g.doc.select("//table/tbody/tr"):
    i += 1
    if i == 1:
        continue
    try:
        separator = el.select("./td/center").text()
        separator = separator.encode("utf-8")
        if separator == "Рейсы с окончательным статусом":
            continue
    except:
        try:
            headOfTable = el.select("./th").text()
            continue
        except:
            pass
    arrival = getDataFromDocumentARH(el, nowTime)
    arrivals.append(arrival)

todayDepartureParams = {
    "date":currentTimeStamp,
    "type":"departure"
}

resp = g.go(urlARH, post=todayDepartureParams)

for el in g.doc.select("//table/tbody/tr"):
    i += 1
    if i == 1:
        continue
    try:
        separator = el.select("./td/center").text()
        separator = separator.encode("utf-8")
        if separator == "Рейсы с окончательным статусом":
            continue
    except:
        try:
            headOfTable = el.select("./th").text()
            continue
        except:
            pass
    departure = getDataFromDocumentARH(el, nowTime, True)
    departures.append(departure)

# Tomorrow
tomorrowDateTime = nowTime + timedelta(days=1)
tomorrowTimeStamp = getTimeStampFromDateTime(tomorrowDateTime)
todayArrivalsParams = {
    "date":tomorrowTimeStamp,
    "type":"arrival"
}

resp = g.go(urlARH, post=todayArrivalsParams)

i = 0
for el in g.doc.select("//table/tbody/tr"):
    i += 1
    if i == 1:
        continue
    try:
        separator = el.select("./td/center").text()
        separator = separator.encode("utf-8")
        if separator == "Рейсы с окончательным статусом":
            continue
    except:
        try:
            headOfTable = el.select("./th").text()
            continue
        except:
            pass
    arrival = getDataFromDocumentARH(el, tomorrowDateTime)
    arrivals.append(arrival)

todayDepartureParams = {
    "date":tomorrowTimeStamp,
    "type":"departure"
}

resp = g.go(urlARH, post=todayDepartureParams)

for el in g.doc.select("//table/tbody/tr"):
    i += 1
    if i == 1:
        continue
    try:
        separator = el.select("./td/center").text()
        separator = separator.encode("utf-8")
        if separator == "Рейсы с окончательным статусом":
            continue
    except:
        try:
            headOfTable = el.select("./th").text()
            continue
        except:
            pass
    departure = getDataFromDocumentARH(el, tomorrowDateTime, True)
    departures.append(departure)

resultARH = {}
resultARH["airport_id"] = "ARH"
resultARH["departures"] = departures
resultARH["arrivals"] = arrivals

jsonResult = json.dumps(resultARH)
#print jsonResult