# boot.py - runs on boot-up

from machine import Pin
import network
import ntptime

import esp
esp.osdebug(None)

import gc
gc.collect()

ssid = 'Nushrat'
password = '12345678'

station = network.WLAN(network.STA_IF)

station.active(True)
station.connect(ssid, password)

while station.isconnected() == False:
  pass

print('Connection successful')
print(station.ifconfig())

# synchronize the RTC with the time from an NTP server
ntptime.settime()

