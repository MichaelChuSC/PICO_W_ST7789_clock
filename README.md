# PICO_W_ST7789_clock
WiFi clock with ST7789 and PICO W

Hardware:
1. PICO 2/ PICO 2W
2. 2.4 inch IPS LCD module 240x320 interface SPI drive ST7789

Software:
1. PICO W firmware
2. ST7789 micropython module (https://github.com/devbis/st7789py_mpy)

Remark:
1. Solar24 data from 2025-2035
2. Temperature and humity inforamtion by json (from Hong Kong Observatory)
3. Lunar date information by json(https://www.iamwawa.cn/nongli)

Pin connection:
ST7789|PICO
------|---------------------------
BL    |3V3
CS    |GND
DC    |GP13  pin no 17 -SPI1 CSn  
RES   |GP12  pin no 16 -SPI1 Rx  
SDA   |GP11  pin no 15 -SPI1 Tx  
SCL   |GP10  pin no 14 -SPI1 SCK 
VCC   |3V3
GND   |GND







