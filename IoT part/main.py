import picoweb
import json
from machine import ADC, Pin, SoftI2C
from neopixel import NeoPixel
from lib.scd4x import SCD4X
from lib.sh1107 import SH1107, SH1107_I2C
import lib.aiorepl as aiorepl
import struct
import network
import time, ntptime
import urequests
import bluetooth
from micropython import const
import ntptime
import uasyncio as asyncio
import ble_simple_peripheral


i2c = SoftI2C(sda=Pin(23), scl=Pin(22))


try:
    scd4x = SCD4X(i2c)
    scd4x.start_periodic_measurement()
except Exception as ex:
    print("Error: SCD41 sensor is not connected " + str(ex))
    scd4x = None
    
try:
    display = SH1107_I2C(128, 64, i2c)
except Exception as ex:
    print("Error: SH1107 is not connected, or maybe RST button is constantly pressed?" + str(ex))
    display = None
station = network.WLAN(network.STA_IF)

def display_coro():
    
    display.fill(0)
    localtime = time.localtime(time.mktime(time.localtime())+3600) # winter time
        #        localtime = time.localtime(time.mktime(time.localtime())+7200) # summer time
    timeISO8601 = f"{localtime[2]:0>2d}/{localtime[1]:0>2d} {localtime[3]:0>2d}:{localtime[4]:0>2d}:{localtime[5]:0>2d}"
    display.text(f"{timeISO8601}" , 0, 9, 1)
    if scd4x.temperature:
        display.text(f"{scd4x.temperature:.1f} *C" , 0, 18, 1)
    if scd4x.relative_humidity:
        display.text(f"{scd4x.relative_humidity:.1f} %RH" , 0, 27, 1)
    if scd4x.CO2:
        display.text(f"{scd4x.CO2} ppm" , 0, 36, 1)
    if station.isconnected():
        display.text(f"{station.ifconfig()[0]}" , 0, 45, 1)
    display.show()
    
display_coro()


import uasyncio as asyncio

global presence 
presence= False

# Define a global variable to hold the JSON data
data = {}

# Define a coroutine that updates the JSON data every second
async def update_data():
    global data
    global presence
    
    while True:
        temperature = " "
        if scd4x.temperature:
            temperature = f"{scd4x.temperature:.1f} *C"

        humidity = " "
        if scd4x.relative_humidity:
            humidity = f"{scd4x.relative_humidity:.1f} %RH"

        CO2 = " "
        if scd4x.CO2:
            CO2 = f"{scd4x.CO2} ppm"
            
        
        localtime = time.localtime(time.mktime(time.localtime())+3600) # winter time
        #        localtime = time.localtime(time.mktime(time.localtime())+7200) # summer time
        timeISO8601 = f"{localtime[2]:0>2d}/{localtime[1]:0>2d} {localtime[3]:0>2d}:{localtime[4]:0>2d}:{localtime[5]:0>2d}"
        
        data = {
            "temperature": temperature,
            "humidity": humidity,
            "CO2": CO2,
            "time": timeISO8601,
            "presence": presence
            
        }

        # Wait for a second before updating again
        await asyncio.sleep(1)

# Define a coroutine that displays the data on the screen
async def display_data():
    while True:
        display_coro()
        await asyncio.sleep(1)
        

# Define a coroutine that updates the presence variable with BLE data
async def ble_connect():
    ble = bluetooth.BLE()
    p = ble_simple_peripheral.BLESimplePeripheral(ble)
    global presence
    while True:
        presence = p.presence
        await asyncio.sleep(0.1)

# Initialize the webserver
app = picoweb.WebApp(__name__)

# Define a route that serves the temperature data as JSON
@app.route("/data")
def get_data(req, resp):
    global data
    yield from picoweb.jsonify(resp, data)

# Start the coroutines
loop = asyncio.get_event_loop()
loop.create_task(update_data())
loop.create_task(display_data())
loop.create_task(ble_connect())

# Start the webserver
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=80)