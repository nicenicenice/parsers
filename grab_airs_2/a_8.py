from Spider8 import *

#logging.basicConfig(level=logging.DEBUG)
bot = ExampleSpider(
    thread_number=8,
    network_try_limit = 3
)
bot.run()

resultBNE = {}
resultBNE["airport_id"] = "BNE"
resultBNE["departures"] = bot.departures
resultBNE["arrivals"] = bot.arrivals

jsonResult = json.dumps(resultBNE)
print jsonResult