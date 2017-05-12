# -*- coding: utf-8 -*-

from grab import Grab
import json
from datetime import datetime, timedelta
import time
import re
import sys

ARRIVED = "arrived"
ESTIMATED = "estimated"
GO_TO_GATE = "go to gate"
AIRBORNE = "airborne"
GATE = "gate"
TAXIED = "taxied"
EARLIER = "earlier"
ON_TIME = "on time"
LAST_CALL = "last call"
NEW_TIME = "new time"
ARRIVES = "arrives"
DELAYED_UNTIL = "delayed until"

FINALL_CALL = "final call"
GO_TO = "go to"

PRIBIL = "Прибыл"
OTPRAVLEN = "Отправлен"
PO_RASPISANIYU = "По расписанию"

ATTERRATO = "atterrato"
PARTITO = "partito"
IMBARCO = "imbarco"
CANCELLATO = "cancellato"

APPROACH = "approach"
NEW_DEPT = "new dept"

CLOSED = "closed"
CONFIRMED = "confirmed"
NEW_GATE = "new gate"

EN_STATUS = "en vol"
PR_STATUS = "pr"
ARRIV_STATUS = "arriv"
ANNUL_STATUS = "annul"

LATE = "late"
GATE_CLOSED = "gate closed"
FINAL_CALL = "final call"
GATE_OPEN = "gate open"

ARRIV_ = "arriv?"
D_COLL_ = "d?coll?"
ENREGISTREMENT_FERM = "Enregistrement Ferm?"
EMBARQUEMENT = "embarquement"
ENREGISTREMENT_OUVERT = "enregistrement ouvert"
TERMIN_ = "termin?"
RETARD_ = "retard?"
ANNUL = "annul?"

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

        GATE_CLOSED: OUTGATE,
        FINAL_CALL: BOARDING,
        GATE_OPEN: BOARDING,
        LATE: DELAYED,

        CLOSED: OUTGATE,
        NEW_GATE: BOARDING,
        CONFIRMED: EXPECTED,

        FINALL_CALL: BOARDING,
        GO_TO: BOARDING,

        PR_STATUS: SCHEDULED,
        ANNUL_STATUS: CANCELLED,
        EN_STATUS: EXPECTED,
        ARRIV_STATUS: LANDED,

        ARRIV_: LANDED,
        D_COLL_: DEPARTED,
        ENREGISTREMENT_OUVERT: CHECKIN,
        EMBARQUEMENT: BOARDING,
        TERMIN_: CANCELLED,
        RETARD_: DELAYED,
        ENREGISTREMENT_FERM: BOARDING,
        ANNUL: CANCELLED,

        NEW_DEPT: BOARDING,
        APPROACH: EXPECTED,

        ATTERRATO: LANDED,
        PARTITO: DEPARTED,
        IMBARCO: BOARDING,
        CANCELLATO: CANCELLED,

        PRIBIL: LANDED,
        OTPRAVLEN: DEPARTED,
        PO_RASPISANIYU: SCHEDULED,

        ESTIMATED: EXPECTED,
        AIRBORNE: DEPARTED,
        GATE: OUTGATE,
        TAXIED: OUTGATE,
        EARLIER: SCHEDULED,
        ARRIVED: LANDED,
        ON_TIME: SCHEDULED,
        LAST_CALL: BOARDING,
        ARRIVES: EXPECTED,
        DELAYED_UNTIL: DELAYED
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


arResult = []
g = Grab(connect_timeout=95, timeout=95)

#ABZ
try:
    urlABZ = "https://www.aberdeenairport.com/flight-information/"
    g.go(urlABZ)

    departures = []
    arrivals = []

    datePattern = "%Y-%m-%d %H:%M:%S"

    for el in g.doc.select('//*[@id="arrivals-departures__arrivals"]/ul/li'):
        scheduled = ""
        flightno = ""
        status = ""
        actual = ""
        estimated = ""
        summaryFullTime = ""
        rawStatus = ""
        numGate = -1

        try:
            status = el.select('.//div[contains(@class, "summary")]//div//span').text()
            rawStatus = str.lower(status)

            status = fixStatus(rawStatus)
            if status == "":
                status = rawStatus

            if status == GO_TO_GATE:
                status = BOARDING
                numGate = el.select('.//div[contains(@class, "summary")]//div/p/text()').text()
            else:
                try:
                    summaryShortTime = el.select('.//div[contains(@class, "summary")]//div/p/text()').text()

                    h = int(summaryShortTime[:2])
                    m = int(summaryShortTime[3:])

                    nowTime = datetime.now()
                    isFlightWillTommorow = False

                    if len(arrivals) > 0:
                        if nowTime.hour > 16 and arrivals[0]["status"] == SCHEDULED:
                            isFlightWillTommorow = True
                    elif nowTime.hour > 16 and status == SCHEDULED:
                        isFlightWillTommorow = True

                    flightTime = nowTime.replace(hour=h, minute=m, second=0)
                    if isFlightWillTommorow:
                        flightTime += timedelta(days=1)

                    summaryFullTime = flightTime.strftime(datePattern)
                except:
                    summaryFullTime = ""

            if status == LANDED:
                actual = summaryFullTime
            elif status == EXPECTED:
                estimated = summaryFullTime
            elif status == DEPARTED:
                actual = summaryFullTime

        except:
            status = ""

        if len(status) <= 0:
            status = SCHEDULED

        try:
            scheduledShortTime = el.select('.//div[contains(@class, "time")]/div/p/text()').text()
            h = int(scheduledShortTime[:2])
            m = int(scheduledShortTime[3:])

            nowTime = datetime.now()
            isFlightWillTommorow = False

            if len(arrivals) > 0:
                if nowTime.hour > 16 and arrivals[0]["status"] == SCHEDULED:
                    isFlightWillTommorow = True
            elif nowTime.hour > 16 and status == SCHEDULED:
                isFlightWillTommorow = True

            flightTime = nowTime.replace(hour=h, minute=m, second=0)
            if isFlightWillTommorow:
                flightTime += timedelta(days=1)

            scheduled = flightTime.strftime(datePattern)
        except:
            scheduled = ""

        try:
            flightno = el.select('.//div[contains(@class, "carrier")]//span').text()
        except:
            flightno = ""

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
        if numGate >= 0:
            arrival["gate"] = numGate
        arrivals.append(arrival)

    for el in g.doc.select('//*[@id="arrivals-departures__departures"]/ul/li'):
        scheduled = ""
        flightno = ""
        status = ""
        actual = ""
        estimated = ""
        summaryFullTime = ""
        rawStatus = ""
        numGate = -1

        try:
            status = el.select('.//div[contains(@class, "summary")]//div//span').text()
            rawStatus = str.lower(status)

            status = fixStatus(rawStatus)
            if status == "":
                status = rawStatus

            if status == GO_TO_GATE:
                status = BOARDING
                numGate = el.select('.//div[contains(@class, "summary")]//div/p/text()').text()
            else:
                try:
                    summaryShortTime = el.select('.//div[contains(@class, "summary")]//div/p/text()').text()

                    h = int(summaryShortTime[:2])
                    m = int(summaryShortTime[3:])

                    nowTime = datetime.now()
                    isFlightWillTommorow = False

                    if len(departures) > 0:
                        if nowTime.hour > 16 and departures[0]["status"] == SCHEDULED:
                            isFlightWillTommorow = True
                    elif nowTime.hour > 16 and status == SCHEDULED:
                        isFlightWillTommorow = True

                    flightTime = nowTime.replace(hour=h, minute=m, second=0)
                    if isFlightWillTommorow:
                        flightTime += timedelta(days=1)

                    summaryFullTime = flightTime.strftime(datePattern)
                except:
                    summaryFullTime = ""

            if status == LANDED:
                actual = summaryFullTime
            elif status == EXPECTED:
                estimated = summaryFullTime
            elif status == DEPARTED:
                actual = summaryFullTime

        except:
            status = ""

        if len(status) <= 0:
            status = SCHEDULED

        try:
            scheduledShortTime = el.select('.//div[contains(@class, "time")]/div/p/text()').text()
            h = int(scheduledShortTime[:2])
            m = int(scheduledShortTime[3:])

            nowTime = datetime.now()
            isFlightWillTommorow = False

            if len(departures) > 0:
                if nowTime.hour > 16 and departures[0]["status"] == SCHEDULED:
                    isFlightWillTommorow = True
            elif nowTime.hour > 16 and status == SCHEDULED:
                isFlightWillTommorow = True

            flightTime = nowTime.replace(hour=h, minute=m, second=0)
            if isFlightWillTommorow:
                flightTime += timedelta(days=1)

            scheduled = flightTime.strftime(datePattern)
        except:
            scheduled = ""

        try:
            flightno = el.select('.//div[contains(@class, "carrier")]//span').text()
        except:
            flightno = ""

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
        if numGate >= 0:
            departure["gate"] = numGate
        departures.append(departure)

    resultABZ = {}
    resultABZ["airport_id"] = "ABZ"
    resultABZ["departures"] = departures
    resultABZ["arrivals"] = arrivals
    arResult.append(resultABZ)
except:
    pass

#ABA
try:
    urlABA = "http://abakan.aero/"
    resp = g.go(urlABA)

    departures = []
    arrivals = []

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
    arResult.append(resultABA)
except:
    pass


#AES
try:
    departures = []
    arrivals = []

    def getDataFromDocumentAES(flight, isDeparture):
        scheduled = ""
        flightno = ""
        status = ""
        actual = ""
        estimated = ""
        rawStatus = ""
        gateNumber = -1
        codeShares = []

        try:
            dateFromJson = str(flight['Date'] + " " + flight['ScheduledTime'])
            dateTimeFromJson = datetime.strptime(dateFromJson, '%Y%m%d %H:%M')
            datePattern = "%Y-%m-%d %H:%M:%S"
            scheduled = dateTimeFromJson.strftime(datePattern)
        except:
            scheduled = ""

        try:
            flightno = flight['FlightId']
        except:
            flightno = ""

        if isDeparture:
            try:
                gateNumber = flight['Gate']
            except:
                gateNumber = -1

        try:
            rawStatusString = str(flight['Status'])

            m = re.search("([a-zA-Z]+\s[a-zA-Z]*)\s?(\d{2}[:]\d{2})?", rawStatusString)

            if m:
                rawStatus = str.lower(m.groups()[0]).strip()
                statusTime = ""

                if m.groups()[1] is not None:
                    dateFromJson = flight['Date'] + " " + m.groups()[1]
                    dateTimeFromJson = datetime.strptime(dateFromJson, '%Y%m%d %H:%M')
                    datePattern = "%Y-%m-%d %H:%M:%S"
                    statusTime = dateTimeFromJson.strftime(datePattern)

                if rawStatus == NEW_TIME:
                    status = EXPECTED
                    estimated = statusTime

                if rawStatus == ARRIVED:
                    status = LANDED
                    actual = statusTime

                if rawStatus == DEPARTED:
                    status = DEPARTED
                    actual = statusTime

                if len(status) <= 0:
                    status = fixStatus(rawStatus)
        except:
            status = ""
            actual = ""
            estimated = ""
            rawStatus = ""

        if len(status) <= 0:
            status = SCHEDULED

        try:
            if len(flight['CodeShares']) > 0:
                codeShares = flight['CodeShares']
        except:
            codeShares = []

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
        if gateNumber >= 0:
            result["gate"] = gateNumber
        return result


    datePatternUrl = "%Y-%m-%dT%H:%M"
    tommotowTimeUrl = datetime.now() + timedelta(days=1)
    fourHoursAgoTimesUrl = datetime.now() - timedelta(hours=5)

    formatedTommotowTimeUrl = tommotowTimeUrl.strftime(datePatternUrl)
    formatedFourHoursAgoTimesUrl = fourHoursAgoTimesUrl.strftime(datePatternUrl)

    ## Arrivals
    urlAESArrivals = "https://avinor.no/Api/Flights/Airport/AES?direction=a&start="\
                     + formatedFourHoursAgoTimesUrl + "&end=" + formatedTommotowTimeUrl + "&language=en"
    resp = g.go(urlAESArrivals)

    jsonResponse = json.loads(resp.body)

    for flight in jsonResponse['Flights']:
        arrival = getDataFromDocumentAES(flight, False)
        arrivals.append(arrival)

    ## Departures
    urlAESDepartures = "https://avinor.no/Api/Flights/Airport/AES?direction=d&start=" \
                       + formatedFourHoursAgoTimesUrl + "&end=" + formatedTommotowTimeUrl + "&language=en"
    resp = g.go(urlAESDepartures)
    jsonResponse = json.loads(resp.body)
    for flight in jsonResponse['Flights']:
        departure = getDataFromDocumentAES(flight, True)
        departures.append(departure)

    resultAES = {}
    resultAES["airport_id"] = "AES"
    resultAES["departures"] = departures
    resultAES["arrivals"] = arrivals
    arResult.append(resultAES)
except:
    pass

#AMM
try:
    departures = []
    arrivals = []

    def getDataFromDocumentAMM(el):
        scheduled = ""
        flightno = ""
        status = ""
        actual = ""
        estimated = ""
        rawStatus = ""

        try:
            flightno = el.select('.//td[1]').text()
        except:
            flightno = ""
        try:
            scheduled = el.select('.//td[3]').text() + ":00"
        except:
            scheduled = "'"
        try:
            estimated = el.select('.//td[4]').text() + ":00"
        except:
            estimated = ""
        try:
            rawStatus = str.lower(el.select('.//td[5]').text())
            status = fixStatus(rawStatus)
        except:
            rawStatus = ""

        if status == "":
            status = SCHEDULED

        result = {
            "flightno": flightno,
            "scheduled": scheduled,
            "estimated": estimated,
            "status": status,
            "raw_status": rawStatus
        }
        return result

    urlAMMArrivals = "http://www.qaiairport.com/en/flights_schedule/arrivals?type=arrivals&from_city=&date=&flight_number=&airline="
    resp = g.go(urlAMMArrivals)

    for el in g.doc.select('//*[@id="block-system-main"]//tbody/tr'):
        arrival = getDataFromDocumentAMM(el)
        arrivals.append(arrival)


    urlAMMDepature = "http://www.qaiairport.com/en/flights_schedule/departures?type=departures&from_city=&date=&flight_number=&airline="
    resp = g.go(urlAMMDepature)

    for el in g.doc.select('//*[@id="block-system-main"]//tbody/tr'):
        departure = getDataFromDocumentAMM(el)
        departures.append(departure)

    resultAMM = {}
    resultAMM["airport_id"] = "AMM"
    resultAMM["departures"] = departures
    resultAMM["arrivals"] = arrivals
    arResult.append(resultAMM)
except:
    pass

#AIO
try:
    departures = []
    arrivals = []

    def getDataFromDocumentAOI(xPath):
        scheduled = ""
        flightno = ""
        status = ""
        actual = ""
        estimated = ""
        rawStatus = ""

        try:
            flightno = g.doc.select(xPath + '//td[3]').text()
        except:
            flightno = ""
        try:
            scheduled = getFullDate(g.doc.select(xPath + '//td[4]').text(), True)
        except:
            scheduled = ""
        try:
            estimated = getFullDate(g.doc.select(xPath + '//td[5]').text(), True)
        except:
            estimated = ""
        try:
            rawStatus = str.lower(g.doc.select(xPath + '//td[6]').text())
            status = fixStatus(rawStatus)
        except:
            status = ""
            rawStatus = ""

        if len(status) <= 0:
            status = SCHEDULED

        result = {
            "flightno": flightno,
            "scheduled": scheduled,
            "status": status,
            "raw_status": rawStatus
        }

        if estimated != "":
            result["estimated"] = estimated

        return result

    urlAOIArrivals = "http://www.aeroportomarche.it/en/Passengers/Flights-info/Real-time-flights"
    resp = g.go(urlAOIArrivals)

    theEnd = False
    i = 1
    while not theEnd:
        xPath = '//*[@id="voliPartenze"]/thead/following-sibling::tr[' + str(i) + ']'
        try:
            trHtml = g.doc.select(xPath).html()
            i += 1
            arrival = getDataFromDocumentAOI(xPath)
            arrivals.append(arrival)
        except:
            theEnd = True
            break


    theEnd = False
    i = 1
    while not theEnd:
        xPath = '//*[@id="dnn_ctr752_ModuleContent"]//table/thead/following-sibling::tr[' + str(i) + ']'
        try:
            trHtml = g.doc.select(xPath).html()
            i += 1
            departure = getDataFromDocumentAOI(xPath)
            departures.append(departure)
        except:
            theEnd = True
            break


    resultAOI = {}
    resultAOI["airport_id"] = "AOI"
    resultAOI["departures"] = departures
    resultAOI["arrivals"] = arrivals
    arResult.append(resultAOI)
except:
    pass

#ARN
try:
    departures = []
    arrivals = []

    datePatternUrl = "%Y%m%d"
    nowTimeUrl = datetime.now()
    tommorowTimeUrl = nowTimeUrl + timedelta(days=1)

    formatedNowTimeUrl = nowTimeUrl.strftime(datePatternUrl)
    formatedTommorowTimeUrl = tommorowTimeUrl.strftime(datePatternUrl)

    urlARNArrivals = "https://www.swedavia.com/services/publicflightsboard/arrivals/en/ARN/" + formatedNowTimeUrl
    urlARNArrivalsTommorow = "https://www.swedavia.com/services/publicflightsboard/arrivals/en/ARN/" + formatedTommorowTimeUrl

    resp = g.go(urlARNArrivals)
    jsonResponseARN = json.loads(resp.body)

    resp = g.go(urlARNArrivalsTommorow)
    jsonResponseARNTommorow = json.loads(resp.body)

    jsonResponseARN['Flights'] = jsonResponseARN['Flights'] + jsonResponseARNTommorow['Flights']

    for flight in jsonResponseARN['Flights']:

        try:
            flight['ArrivalDateTime']
        except:
            continue

        scheduled = ""
        flightno = ""
        status = ""
        actual = ""
        estimated = ""
        rawStatus = ""

        codeShares = []

        try:
            scheduled = flight['ArrivalDateTime']
            scheduled = scheduled.replace("T", " ")
        except:
            scheduled = ""

        try:
            datePattern = "%Y-%m-%d %H:%M:%S"

            actual = getFullDate(flight['ActualTime'], True)
            actualDateTime = datetime.strptime(actual, datePattern)
            scheduledDateTime = datetime.strptime(scheduled, datePattern)

            actualDateTime = actualDateTime.replace(day=scheduledDateTime.day)  # 2017-04-16 04:45
            yesterdayActualDateTime = actualDateTime - timedelta(days=1)  # 2017-04-15 04:45
            tommorowActualDateTime = actualDateTime + timedelta(days=1)  # 2017-04-15 04:45

            scheduledTimeStampe = time.mktime(scheduledDateTime.timetuple())
            tommorowActualDateTimeStampe = time.mktime(tommorowActualDateTime.timetuple())
            actualTimeStampe = time.mktime(actualDateTime.timetuple())
            actualYesterdayTimeStampe = time.mktime(yesterdayActualDateTime.timetuple())

            diffScheduleWithActual = abs(scheduledTimeStampe - actualTimeStampe)
            diffScheduleWithYesterdayActual = abs(scheduledTimeStampe - actualYesterdayTimeStampe)
            diffScheduleWithTommorowActual = abs(scheduledTimeStampe - tommorowActualDateTimeStampe)

            arDiffs = [diffScheduleWithActual, diffScheduleWithYesterdayActual, diffScheduleWithTommorowActual]
            minDiffVal = min(arDiffs)

            if minDiffVal == diffScheduleWithActual:
                actual = actualDateTime.strftime(datePattern)
            elif minDiffVal == diffScheduleWithYesterdayActual:
                actual = yesterdayActualDateTime.strftime(datePattern)
            elif minDiffVal == diffScheduleWithTommorowActual:
                actual = tommorowActualDateTime.strftime(datePattern)
        except:
            actual = ""

        try:
            estimated = flight['ProbableTime']
            estimated = estimated.replace("T", " ")
        except:
            estimated = ""

        try:
            flightno = flight['FlightNumber']
        except:
            flightno = ""

        try:
            rawStatusString = str(flight['Remark']['RemarkText'])
            m = re.search("([a-zA-Z]+( [a-zA-Z]+)?)?\s?(\d{2}[\:]\d{2})?", rawStatusString)
            if m:
                rawStatus = str.lower(m.groups()[0])
                status = fixStatus(rawStatus)
        except:
            try:
                rawStatusString = str(flight["GateStatus"]["GateStatusText"])
                m = re.search("([a-zA-Z]+( [a-zA-Z]+)?)?\s?(\d{2}[\:]\d{2})?", rawStatusString)
                if m:
                    rawStatus = str.lower(m.groups()[0])
                    status = fixStatus(rawStatus)
            except:
                rawStatus = ""
                status = ""

        if len(status) <= 0:
            status = SCHEDULED

        try:
            if len(flight['CodeShares']) > 0:
                for codeShare in flight['CodeShares']:
                    codeShares.append(codeShare["FlightNumber"])
        except:
            codeShares = []

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

        arrivals.append(arrival)

    urlARNDepartures = "https://www.swedavia.com/services/publicflightsboard/departures/en/ARN/" + formatedNowTimeUrl
    urlARNDeparturesTommorow = "https://www.swedavia.com/services/publicflightsboard/departures/en/ARN/" + formatedTommorowTimeUrl

    resp = g.go(urlARNDepartures)
    jsonResponseARN = json.loads(resp.body)

    resp = g.go(urlARNDeparturesTommorow)
    jsonResponseARNTommorow = json.loads(resp.body)

    jsonResponseARN['Flights'] = jsonResponseARN['Flights'] + jsonResponseARNTommorow['Flights']

    for flight in jsonResponseARN['Flights']:

        try:
            flight['DepartureDateTime']
        except:
            continue

        scheduled = ""
        flightno = ""
        status = ""
        actual = ""
        estimated = ""
        rawStatus = ""
        codeShares = []
        numGate = -1
        checkInDesk = ""

        try:
            scheduled = flight['DepartureDateTime']
            scheduled = scheduled.replace("T", " ")
        except:
            scheduled = ""

        try:
            datePattern = "%Y-%m-%d %H:%M:%S"

            actual = getFullDate(flight['ActualTime'], True)
            actualDateTime = datetime.strptime(actual, datePattern)
            scheduledDateTime = datetime.strptime(scheduled, datePattern)

            actualDateTime = actualDateTime.replace(day=scheduledDateTime.day)  # 2017-04-16 04:45
            yesterdayActualDateTime = actualDateTime - timedelta(days=1)  # 2017-04-15 04:45
            tommorowActualDateTime = actualDateTime + timedelta(days=1)  # 2017-04-15 04:45

            scheduledTimeStampe = time.mktime(scheduledDateTime.timetuple())
            tommorowActualDateTimeStampe = time.mktime(tommorowActualDateTime.timetuple())
            actualTimeStampe = time.mktime(actualDateTime.timetuple())
            actualYesterdayTimeStampe = time.mktime(yesterdayActualDateTime.timetuple())

            diffScheduleWithActual = abs(scheduledTimeStampe - actualTimeStampe)
            diffScheduleWithYesterdayActual = abs(scheduledTimeStampe - actualYesterdayTimeStampe)
            diffScheduleWithTommorowActual = abs(scheduledTimeStampe - tommorowActualDateTimeStampe)

            arDiffs = [diffScheduleWithActual, diffScheduleWithYesterdayActual, diffScheduleWithTommorowActual]
            minDiffVal = min(arDiffs)

            if minDiffVal == diffScheduleWithActual:
                actual = actualDateTime.strftime(datePattern)
            elif minDiffVal == diffScheduleWithYesterdayActual:
                actual = yesterdayActualDateTime.strftime(datePattern)
            elif minDiffVal == diffScheduleWithTommorowActual:
                actual = tommorowActualDateTime.strftime(datePattern)
        except:
            actual = ""

        try:
            estimated = flight['ProbableTime']
            estimated = estimated.replace("T", " ")
        except:
            estimated = ""

        try:
            numGate = flight['Gate']
        except:
            numGate = -1

        try:
            flightno = flight['FlightNumber']
        except:
            flightno = ""

        try:
            rawStatusString = str(flight['Remark']['RemarkText'])
            m = re.search("([a-zA-Z]+( [a-zA-Z]+)?)?\s?(\d{2}[\:]\d{2})?", rawStatusString)
            if m:
                rawStatus = str.lower(m.groups()[0])
                status = fixStatus(rawStatus)
        except:
            try:
                rawStatusString = str(flight["GateStatus"]["GateStatusText"])
                m = re.search("([a-zA-Z]+( [a-zA-Z]+)?)?\s?(\d{2}[\:]\d{2})?", rawStatusString)
                if m:
                    rawStatus = str.lower(m.groups()[0])
                    status = fixStatus(rawStatus)
            except:
                rawStatus = ""
                status = ""

        if len(status) <= 0:
            status = SCHEDULED

        try:
            checkInDesk = flight['Amendments']["CheckInDesk"]
        except:
            checkInDesk = ""

        try:
            if len(flight['CodeShares']) > 0:
                for codeShare in flight['CodeShares']:
                    codeShares.append(codeShare["FlightNumber"])
        except:
            codeShares = []

        departure = {
            "flightno": flightno,
            "scheduled": scheduled,
            "status": status,
            "raw_status": rawStatus
        }

        if str(numGate) != str(-1):
            departure["gate"] = numGate
        if estimated != "":
            departure["estimated"] = estimated
        if actual != "":
            departure["actual"] = actual
        if checkInDesk != "":
            departure["check_in_desks"] = checkInDesk

        departures.append(departure)

    resultARN = {}
    resultARN["airport_id"] = "ARN"
    resultARN["departures"] = departures
    resultARN["arrivals"] = arrivals
    arResult.append(resultARN)
except:
    pass

#ATH
try:
    departures = []
    arrivals = []

    currentTimestamp = int(round(time.time() * 1000))
    urlATH = "https://www.aia.gr/handlers/rtfi.ashx?action=getRtfiJson&cultureId=50&bringRecent=1&timeStampFormat=Fyyyy-FMM-dd+HH-mm&allRecs=1&airportId=&airlineId=&flightNo=&_=" + str(currentTimestamp)
    resp = g.go(urlATH)
    jsonResponseATH = json.loads(resp.body)

    def getDataFromDocumentATH(chunk):
        scheduled = ""
        flightno = ""
        status = ""
        actual = ""
        estimated = ""
        rawStatus = ""
        gate = ""

        try:
            flightno = chunk['FlightNo']
        except:
            flightno = ""
        try:
            rawScheduled = chunk['ScheduledTime']
            scheduled = datetime.strptime(rawScheduled, '%d/%m/%Y %H:%M')
            scheduled = scheduled.strftime(datePattern)
        except:
            scheduled = ""
        try:
            rawEstimated = chunk['EstimatedTime']
            estimated = datetime.strptime(rawEstimated, '%d/%m/%Y %H:%M')
            estimated = estimated.strftime(datePattern)
        except:
            estimated = ""
        try:
            rawStatus = str(chunk['FlightStateName'])
            lowerRawStatus = str.lower(rawStatus)
            status = fixStatus(lowerRawStatus)
        except:
            status = ""

        if len(status) <= 0:
            status = SCHEDULED

        try:
            gate = str(chunk['Gate'])
        except:
            gate = ""

        result = {
            "flightno": flightno,
            "scheduled": scheduled,
            "status": status,
            "raw_status": rawStatus
        }

        if estimated != "":
            result["estimated"] = estimated
        if len(gate) > 0:
            result["gate"] = gate
        return result


    for flight in jsonResponseATH['arrivals']:
        try:
            if len(flight['data']) <= 0:
                continue
        except:
            continue

        for chunk in flight['data']:
            arrival = getDataFromDocumentATH(chunk)
            arrivals.append(arrival)

    for flight in jsonResponseATH['departures']:

        if len(flight['data']) <= 0:
            continue

        for chunk in flight['data']:
            departure = getDataFromDocumentATH(chunk)
            departures.append(departure)

    resultATH = {}
    resultATH["airport_id"] = "ATH"
    resultATH["departures"] = departures
    resultATH["arrivals"] = arrivals
    arResult.append(resultATH)
except:
    pass

#CMN
try:
    departures = []
    arrivals = []

    def getDataFromDocumentCMN(flight):
        scheduled = ""
        flightno = ""
        status = ""
        actual = ""
        estimated = ""
        rawStatus = ""
        codeShares = []

        try:
            arFlightno = str(flight['num_vol']).split(" / ")
            flightno = arFlightno[0]
            if len(arFlightno) > 1:
                for i in range(1, len(arFlightno)):
                    codeShares.append(arFlightno[i])
        except:
            flightno = ""
        try:
            scheduled = flight['date_vol'] + " " + flight['heure_vol'] + ":" + flight['min_vol']

            estimated = scheduled
        except:
            scheduled = ""

        try:
            rawStatus = str(flight['Observation'])
            lowerRawStatus = str.lower(rawStatus)
            status = fixStatus(lowerRawStatus)
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

        if estimated != "":
            result["estimated"] = estimated
        if len(codeShares) > 0:
            result["codeshares"] = codeShares
        return result

    urlCMN = "http://www.onda.ma/layout/set/ajax/onda_horaires/get_list"
    resp = g.go(urlCMN, post={'type': 'arrivees', 'codeAeroport' : 'CMN'})
    jsonResponse = json.loads(resp.body)
    for arHours in jsonResponse:
        flightPerHour = jsonResponse[arHours]
        for flight in flightPerHour:
            arrival = getDataFromDocumentCMN(flight)
            arrivals.append(arrival)

    urlCMN = "http://www.onda.ma/layout/set/ajax/onda_horaires/get_list"
    resp = g.go(urlCMN, post={'type': 'departs', 'codeAeroport' : 'CMN'})
    jsonResponse = json.loads(resp.body)
    for arHours in jsonResponse:
        flightPerHour = jsonResponse[arHours]
        for flight in flightPerHour:
            departure = getDataFromDocumentCMN(flight)
            departures.append(departure)

    resultCMN = {}
    resultCMN["airport_id"] = "CMN"
    resultCMN["departures"] = departures
    resultCMN["arrivals"] = arrivals
    arResult.append(resultCMN)
except:
    pass

#CNX
try:
    departures = []
    arrivals = []
    g = Grab(connect_timeout=100, timeout=100)

    datePattern = "%Y-%m-%d"
    nowTime = datetime.now()
    formatedNowTime = nowTime.strftime(datePattern)

    urlCNXArrived = "http://chiangmaiairportthai.com/en/278-passenger-arrivals?after_search=1&page=&date=" + formatedNowTime + "&airport=0&flight_no=&start_time=00%3A00&end_time=23%3A59&airline=0"
    resp = g.go(urlCNXArrived)


    def getDataFromDocument(el):
        scheduled = ""
        flightno = ""
        status = ""
        actual = ""
        estimated = ""
        rawStatus = ""
        gate = ""

        try:
            flightno = str(el.select('.//td[2]').text())
            if len(flightno) <= 0:
                return -1
        except:
            return -1

        try:
            rawScheduled = str(el.select('.//td[3]').text())
            scheduled = getFullDate(rawScheduled, True)
        except:
            scheduled = ""

        try:
            estiActialTime = str(el.select('.//td[4]').text())
            estiActialTime = getFullDate(estiActialTime, True)
        except:
            estiActialTime = ""

        try:
            gateTerminal = str(el.select('.//td[6]').text())
            m = re.search("Gate(\d{2}) Terminal \w?", gateTerminal)
            if m:
                gate = str.lower(m.groups()[0])
        except:
            gate = ""

        try:
            rawStatus = str(el.select('.//td[7]/span').text())
            rawStatus = str.lower(rawStatus)
            status = fixStatus(rawStatus)

            if len(rawStatus) > 0:
                if rawStatus == CONFIRMED:
                    estimated = estiActialTime
                elif rawStatus == DELAYED:
                    estimated = estiActialTime
                if estimated == "":
                    actual = estiActialTime
        except:
            status = ""
            rawStatus = ""
            actual = ""
            estimated = ""

        if len(status) <= 0:
            status = SCHEDULED

        result = {
            "flightno": flightno,
            "scheduled": scheduled,
            "status": status,
            "raw_status": rawStatus
        }
        if gate != "":
            result["gate"] = gate
        if estimated != "":
            result["estimated"] = estimated
        if actual != "":
            result["actual"] = actual

        return result


    urlCNXArrived = "http://chiangmaiairportthai.com/en/278-passenger-arrivals?after_search=1&page=&date=" + formatedNowTime + "&airport=0&flight_no=&start_time=00%3A00&end_time=23%3A59&airline=0"
    resp = g.go(urlCNXArrived)

    for el in g.doc.select('//*[@id="mid-container"]//table/tbody/tr'):
        arrival = getDataFromDocument(el)
        if arrival != -1:
            arrivals.append(arrival)

    urlCNXDepartured = "http://www.chiangmaiairportthai.com/en/279-passenger-departures?after_search=1&page=&date=" + formatedNowTime + "&airport=0&flight_no=&start_time=00%3A00&end_time=23%3A59&airline=0"
    resp = g.go(urlCNXDepartured)

    for el in g.doc.select('//*[@id="mid-container"]//table/tbody/tr'):
        departure = getDataFromDocument(el)
        if departure != -1:
            departures.append(departure)

    resultCNX = {}
    resultCNX["airport_id"] = "CNX"
    resultCNX["departures"] = departures
    resultCNX["arrivals"] = arrivals
    arResult.append(resultCNX)
except:
    pass

#ALG
try:

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

        arrivals.append(arrival)


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
        departures.append(departure)

    resultALG = {}
    resultALG["airport_id"] = "ALG"
    resultALG["departures"] = departures
    resultALG["arrivals"] = arrivals
    arResult.append(resultALG)
except:
    pass

print arResult