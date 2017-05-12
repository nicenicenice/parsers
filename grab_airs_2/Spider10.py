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
    urlPER = "https://www.perthairport.com.au/flights/departures-and-arrivals?Nature=Departure"
    g = Grab(connect_timeout=39, timeout=40, url=urlPER)

    arrivals = []
    departures = []
    BOARDING_SOON = "boarding soon"
    FLIGHT_CLOSED = "flight closed"
    CHECKIN_OPEN = "check-in open"
    CHECKIN_CLOSE = "check-in close"
    CONFIRMED = "confirmed"
    ON_TIME = "on-time"
    GO_TO_GATE = "go to gate"
    CLOSED = "closed"

    EARLY = "early"
    UNKNOWN = "unknown"
    CHECK_IN = "check-in"
    BOARDING_CLOSED = "boarding closed"
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

    siteDateTime = ""
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
            self.GO_TO_GATE : self.BOARDING,
            self.CLOSED:self.BOARDING,
            self.BOARDING_SOON:self.CHECKIN,
            self.EARLY: self.SCHEDULED,
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
            self.LATE: self.DELAYED,
            "":self.SCHEDULED
        }.get(status, self.UNKNOWN)

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

    def getTimeStampFromDateTime(datetime):
        return int(time.mktime(datetime.timetuple()) + datetime.microsecond / 1E6)

    def getDataFromDocumentPER(self, flight, dateTime, isDeparture=False):
        scheduled = ""
        flightno = ""
        status = ""
        actual = ""
        estimated = ""
        rawStatus = ""
        codeshares = []
        terminal = ""
        luggage = ""
        gate = ""

        try:
            codeshares = flight['CodeShares']
        except:
            codeshares

        try:
            rawStatus = str(flight['Remark'])
            rawStatus = str.lower(rawStatus).strip()
            status = self.fixStatus(rawStatus)
        except:
            status = ""

        if status == "":
            status = self.SCHEDULED

        try:
            flightno = str(flight['FlightNumber'])
        except:
            flightno = ""

        try:
            rawScheduled = flight['ScheduledTime']
            h = int(rawScheduled[:2])
            m = int(rawScheduled[3:])
            scheduleDateTime = dateTime.replace(hour=h, minute=m, second=0)
            scheduled = scheduleDateTime.strftime(self.datePattern)
        except:
            scheduled = ""

        try:
            rawAddTime = flight['EstimatedTime']
            addTime = self.getFullDate(rawAddTime, scheduleDateTime)
            if status == self.LANDED or status == self.DEPARTED:
                actual = addTime
            else:
                estimated = addTime
        except:
            actual = ""
            estimated = ""
            addTime = ""

        try:
            terminal = flight['Terminal']
        except:
            terminal = ""

        if isDeparture:
            try:
                gate = flight['Gate']
            except:
                gate = ""

        result = {
            "flightno": flightno,
            "scheduled": scheduled,
            "status": status,
            "raw_status": rawStatus
        }

        if len(codeshares) > 0:
            result["codeshares"] = codeshares
        if terminal != "":
            result["terminal"] = terminal
        if luggage != "":
            result["luggage"] = luggage
        if gate != "":
            result["gate"] = gate
        if estimated != "":
            result["estimated"] = estimated
        if actual != "":
            result["actual"] = actual
        return result

    def task_generator(self):

        # get prepared date
        resp = self.g.go(self.urlPER)
        todayParam = self.g.doc.select("//*[@id='day']/option[1]/@value").text()
        tomorrowParam = self.g.doc.select("//*[@id='day']/option[2]/@value").text()
        __RequestVerificationToken = self.g.doc.select("//*[@id='flightSearch']/input/@value").text()


        postParams = {
            "scController": "Flights",
            "scAction": "GetFlightResults",
            "Date": "",
            "Time": "",
            "Nature": "",
            "DomInt": "",
            "Query": "",
            "Terminal": "",
            "__RequestVerificationToken": __RequestVerificationToken
        }

        todayArrivalPostParams = postParams.copy()
        todayArrivalPostParams["Nature"] = "Arrivals"
        todayArrivalPostParams["Date"] = todayParam

        todayDeparturePostParams = postParams.copy()
        todayDeparturePostParams["Nature"] = "Departures"
        todayDeparturePostParams["Date"] = todayParam

        tomorrowArrivalPostParams = postParams.copy()
        tomorrowArrivalPostParams["Nature"] = "Arrivals"
        tomorrowArrivalPostParams["Date"] = tomorrowParam

        tomorrowDeparturePostParams = postParams.copy()
        tomorrowDeparturePostParams["Nature"] = "Departures"
        tomorrowDeparturePostParams["Date"] = tomorrowParam

        params = [todayArrivalPostParams, todayDeparturePostParams, tomorrowArrivalPostParams, tomorrowDeparturePostParams]

        i = 0
        for item in params:
            i += 1
            self.g.setup(url=self.urlPER, post=item)
            yield Task('handle', grab=self.g, param=item, num_task=i)

    def task_handle(self, grab, task):
        jsonResponse = json.loads(grab.response.body)

        dateSelectPattern = "%m/%d/%Y"
        dateTime = datetime.strptime(task.param["Date"], dateSelectPattern)

        if task.param["Nature"] == "Arrivals":
            for flight in jsonResponse['Results']:
                arrival = self.getDataFromDocumentPER(flight, dateTime)
                self.arrivals.append(arrival)
        else:
            for flight in jsonResponse['Results']:
                departure = self.getDataFromDocumentPER(flight, dateTime)
                self.departures.append(departure)

                startUrl = "https://www.perthairport.com.au/flights/departures-and-arrivals/"
                month = str(dateTime.month)
                day = str(dateTime.day)
                if len(month) == 1:
                    month = "0" + month
                if len(day) == 1:
                    day = "0" + day
                url = startUrl + str.lower(departure["flightno"]) + str(dateTime.year) + month + day + "d"

                #self.g = Grab(connect_timeout=39, timeout=40, url=url)
                #yield Task('detail', grab=self.g)

    """def task_detail(self, grab, task):
        try:
            #print grab.response.body
            print grab.doc.select("//div[contains(@class, 'flight-card_desc-supp')]/p[2]").text()
            #print grab.doc.select("/html/body/div/div[4]/div/div/div/div[2]/div/div/div[2]/div[1]/div/div[2]/div/div[2]/p[2]").html()
        except:
            pass"""


