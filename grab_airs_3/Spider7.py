# coding: utf-8

from grab import Grab
import json
from datetime import datetime, timedelta
import logging
import time
import warnings
warnings.filterwarnings('ignore')

from grab.spider import Spider, Task

class ExampleSpider(Spider):
    # Список страниц, с которых Spider начнёт работу
    # для каждого адреса в этом списке будет сгенерировано
    # задание с именем initial
    jsonResult = {}
    COUNTER = 0
    CHECKIN_OPEN = "ch-in open"
    CHECKIN_CLOSE = "ch-in close"
    CONFIRMED = "confirmed"

    UNKNOWN = "unknown"
    CHECK_IN = "check-in"
    BOARDING_CLOSED = "boarding closed"
    ON_TIME = "on time"
    CANCELED = "canceled"
    AIRBORNE = "airborne"
    ESTIMSTED = "estimated"

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


    def fixStatus(self, status):
        return {
            self.SCHEDULED: self.SCHEDULED,
            self.DELAYED: self.DELAYED,
            self.CANCELLED: self.CANCELLED,
            self.CHECKIN: self.CHECKIN,
            self.BOARDING: self.BOARDING,
            self.OUTGATE: self.OUTGATE,
            self.DEPARTED: self.DEPARTED,
            self.EXPECTED: self.EXPECTED,
            self.LANDED: self.LANDED,

            self.CONFIRMED: self.SCHEDULED,
            self.CHECKIN_CLOSE: self.BOARDING,
            self.CHECKIN_OPEN: self.CHECKIN,
            self.CHECK_IN: self.CHECKIN,
            self.ESTIMSTED: self.EXPECTED,
            self.AIRBORNE: self.DEPARTED,
            self.CANCELED: self.CANCELLED,
            self.BOARDING_CLOSED: self.OUTGATE,
            self.ON_TIME: self.SCHEDULED,
            self.GATE_CLOSED: self.OUTGATE,
            self.FINAL_CALL: self.BOARDING,
            self.GATE_OPEN: self.BOARDING,
            self.ARRIVED: self.LANDED,
            self.LATE: self.DELAYED
        }.get(status, "")

    def getFullDate(self, hourMinute, scheduleDateTime):
        datePattern = "%Y-%m-%d %H:%M:%S"
        nowTime = datetime.now()
        correctDate = scheduleDateTime

        h = int(hourMinute[:2])
        m = int(hourMinute[3:])

        notFormatedTime = correctDate.replace(hour=h, minute=m, second=0)

        if scheduleDateTime.hour > 20 and h < 5:
            notFormatedTime = notFormatedTime + timedelta(days=1)
        elif scheduleDateTime.hour < 5 and h > 20:
            notFormatedTime = notFormatedTime - timedelta(days=1)

        formatedTime = notFormatedTime.strftime(datePattern)
        return formatedTime

    def getTimeStampFromDateTime(self, datetime):
        return int(time.mktime(datetime.timetuple()) + datetime.microsecond / 1E6)

    def getDataFromDocumentBKK(self, el, dateTime):
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
            rawScheduled = el.select('.//td[3]').text()

            h = int(rawScheduled[:2])
            m = int(rawScheduled[3:])

            dateTimeToCorrect = dateTime
            scheduleDateTime = dateTimeToCorrect.replace(hour=h, minute=m, second=0)
            scheduled = scheduleDateTime.strftime(self.datePattern)
        except:
            return -1

        try:
            rawFlightno = el.select('.//td[2]').text()
            flightno = rawFlightno.encode("utf-8")
        except:
            flightno = ""

        try:
            rawStatus = el.select('.//td[7]').text()
            rawStatus = str.lower(rawStatus)
            status = self.fixStatus(rawStatus)
            if status == "" and rawStatus != "":
                status = self.UNKNOWN
        except:
            rawStatus = ""
            status = ""

        if status == "":
            status = self.SCHEDULED

        try:
            rawAdditionTime = el.select('.//td[4]').text()
            additionTime = self.getFullDate(rawAdditionTime, scheduleDateTime)
            if status == self.LANDED or status == self.DEPARTED:
                actual = additionTime
            elif rawStatus == self.CONFIRMED:
                scheduleDateTime = datetime.strptime(scheduled, self.datePattern)
                scheduleTimeStamp = self.getTimeStampFromDateTime(scheduleDateTime)
                additionDateTime = datetime.strptime(additionTime, self.datePattern)
                additionTimeStamp = self.getTimeStampFromDateTime(additionDateTime)
                diff = abs(scheduleTimeStamp - additionTimeStamp)
                if diff >= 15 * 60:
                    status = self.DELAYED
                estimated = additionTime
            else:
                estimated = additionTime
        except:
            actual = ""
            estimated = ""

        try:
            addInfoString = el.select('.//td[6]').text()
            if addInfoString.find("Belt") >= 0 and status != self.CANCELLED:
                luggage = addInfoString[addInfoString.find("Belt") + 5:addInfoString.find("Terminal")].strip()
            if addInfoString.find("Gate") >= 0 and status != self.CANCELLED:
                gate = addInfoString[addInfoString.find("Gate") + 5:addInfoString.find("Gate") + 8].strip()
            if addInfoString.find("Terminal") >= 0:
                terminal = addInfoString[addInfoString.find("Terminal") + 9:addInfoString.find("Terminal") + 11].strip()
        except:
            gate = ""
            terminal = ""
            luggage = ""

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
        if luggage != "":
            result["luggage"] = luggage
        if gate != "":
            result["gate"] = gate
        if terminal != "":
            result["terminal"] = terminal
        return result

    def task_generator(self):

        urlsToGrab = []
        urlPattern = "%Y-%m-%d"
        tomorrowDateTime = self.nowTime + timedelta(days=1)
        todayDate = self.nowTime.strftime(urlPattern)
        tomorrowDate = tomorrowDateTime.strftime(urlPattern)

        bKKDepToday = {
            'url':"http://www.suvarnabhumiairport.com/en/4-passenger-departures?after_search=1&page=&date=" + todayDate + "&airport=0&flight_no=&start_time=00%3A00&end_time=23%3A59&airline=0",
            'is_depart' : True,
            'datetime' : self.nowTime

        }
        bKKArrToday = {
            'url': "http://www.suvarnabhumiairport.com/en/3-passenger-arrivals?after_search=1&page=&date=" + todayDate + "&airport=0&flight_no=&start_time=00%3A00&end_time=23%3A59&airline=0",
            'is_depart': False,
            'datetime': self.nowTime

        }
        bKKDepTomorrow = {
            'url': "http://www.suvarnabhumiairport.com/en/4-passenger-departures?after_search=1&page=&date=" + tomorrowDate + "&airport=0&flight_no=&start_time=00%3A00&end_time=23%3A59&airline=0",
            'is_depart': True,
            'datetime': tomorrowDateTime

        }
        bKKArrTomorrow = {
            'url': "http://www.suvarnabhumiairport.com/en/3-passenger-arrivals?after_search=1&page=&date=" + tomorrowDate + "&airport=0&flight_no=&start_time=00%3A00&end_time=23%3A59&airline=0",
            'is_depart': False,
            'datetime': tomorrowDateTime
        }

        urlsToGrab = [bKKDepToday, bKKArrToday, bKKDepTomorrow, bKKArrTomorrow]

        i = 0
        for item in urlsToGrab:
            i += 1
            g = Grab(connect_timeout=29, timeout=30, url=item["url"])
            yield Task('handle', grab=g, is_depart=item["is_depart"], datetime=item["datetime"], number=i)


    def task_handle(self, grab, task):
        #print "start - " + str(task.number)
        #print datetime.now()
        #print "/n"
        if not task.is_depart:
            for el in grab.doc.select("//*[@id='mid-container']/div/div/div[2]/div[2]/div[1]/table/tbody/tr"):
                arrival = self.getDataFromDocumentBKK(el, task.datetime)
                if arrival == -1:
                    try:
                        flightno = el.select('.//td[2]').text()
                    except:
                        continue
                    if not self.arrivals[len(self.arrivals) - 1].has_key("codeshares"):
                        self.arrivals[len(self.arrivals) - 1]["codeshares"] = []
                    self.arrivals[len(self.arrivals) - 1]["codeshares"].append(flightno)
                else:
                    self.arrivals.append(arrival)
            self.COUNTER += 1
        else:
            for el in grab.doc.select("//*[@id='mid-container']/div/div/div[2]/div[2]/div[1]/table/tbody/tr"):
                departure = self.getDataFromDocumentBKK(el, task.datetime)
                if departure == -1:
                    try:
                        flightno = el.select('.//td[2]').text()
                    except:
                        continue
                    if not self.departures[len(self.departures) - 1].has_key("codeshares"):
                        self.departures[len(self.departures) - 1]["codeshares"] = []
                    self.departures[len(self.departures) - 1]["codeshares"].append(flightno)
                else:
                    self.departures.append(departure)
            self.COUNTER += 1
        #print "finish - " + str(task.number)
        #print datetime.now()
        #print "/n"

