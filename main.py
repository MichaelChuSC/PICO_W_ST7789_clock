'''
st7789py Driver
https://github.com/devbis/st7789py_mpy

To: 1. NTP time
    2. ST7789 display (240x320)
    3. tube font in yellow/black
    4. solar24 data from 2025-2035
    5. Watchdog
    6. Hourly to get temperature and humity by json
    7. Hour and Min in different color
    
Written by: Michael Chu
Date: 3 Mar 2026
'''

from machine import Pin, SPI
from machine import WDT
import os, machine, time, utime
import st7789py as st7789   
import ntptime
import network   # handles connecting to WiFi
import urequests # handles making and servicing network requests
import font.vga1_16x16 as font2
import font.vga16x32 as font3
import font.vga24x24_CH_clock as font_clk

Clk_font_map = '\u9999\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d'\
               '\u5341\u5eff\u5345\u5e74\u6708\u65e5\u661f\u671f\u65f6\u5206'\
               '\u79d2\u9999\u7532\u4e59\u4e19\u4e01\u620a\u5df1\u5e9a\u8f9b'\
               '\u58ec\u7678\u5b50\u4e11\u5bc5\u536f\u8fb0\u5df3\u5348\u672a'\
               '\u7533\u9149\u620c\u4ea5\u6b63\u51ac\u814a\u521d\u7acb\u6625'\
               '\u96e8\u6c34\u9a5a\u87c4\u5206\u6e05\u660e\u8c37\u590f\u5c0f'\
               '\u8292\u7a2e\u81f3\u6691\u5927\u79cb\u8655\u767d\u9732\u5bd2'\
               '\u971c\u964d\u51ac\u96ea\u6eff'

'''
# ST
#7789 |PICO
#-----|---------------------------
#BL   |3V3
#CS   |GND
#DC   |GP13  pin no 17 -SPI1 CSn  
#RES  |GP12  pin no 16 -SPI1 Rx  
#SDA  |GP11  pin no 15 -SPI1 Tx  
#SCL  |GP10  pin no 14 -SPI1 SCK 
#VCC  |3V3
#GND  |GND

'''

spi_no=1
spi_sck=10
spi_mosi=11
spi_miso=8     #not use
st7789_res = 12
st7789_dc  = 13
disp_width = 240
disp_height = 320
CENTER_Y = int(disp_width/2)
CENTER_X = int(disp_height/2)

spi = machine.SPI(spi_no, baudrate=40000000, polarity=1,
                  sck=machine.Pin(spi_sck), mosi=machine.Pin(spi_mosi))
TFT = st7789.ST7789(spi, disp_width, disp_height,
                    reset=machine.Pin(st7789_res, machine.Pin.OUT),
                    dc=machine.Pin(st7789_dc, machine.Pin.OUT))
TFT.rotation(1)

df_BLACK  = 0x0000
df_BLUE   = 0x001F  #(0x00, 0x00, 0xFF)
df_RED    = 0xF800  #(0xFF, 0x00, 0x00)
df_GREEN  = 0x07E0  #(0x00, 0xFF, 0x00)
df_CYAN   = 0x07FF  #(0x00, 0xFF, 0xFF)
df_MAGENTA= 0xF81F  #(0x1F, 0x00, 0x1F)洋紅色
df_YELLOW = 0xFFE0  #(0xFF, 0xFF, 0x00)
df_WHITE  = 0xFFFF  #(0xFF, 0xFF, 0xFF)
df_MAROON = 0x8000  #(0x80, 0x00, 0x00)
df_FOREST = 0x410   #(0x00, 0x80, 0x80)
df_NAVY   = 0x10    #(0x00, 0x00, 0x80) 
df_PURPLE = 0x6875  #(106, 13, 173)紫色 
df_GRAY   = 0x8410  #(0x80, 0x80, 0x80)
df_ORANGE = 0xfd20  #(255,165,0)

df_color = [df_BLUE, df_RED, df_GREEN, df_CYAN, df_MAGENTA,\
            df_YELLOW, df_WHITE , df_MAROON, df_FOREST, df_NAVY ,\
            df_PURPLE, df_GRAY, df_ORANGE, df_BLACK ]
total_col = len(df_color) - 2
exit_col_code = 0

char_font_size   = 24
char_byte_of_row = char_font_size // 8
font_array_byte = 72
buffer = bytearray(font_array_byte)
# routine for print a Chinese Char.
# high bit fo left side print dot
# byte[0] , byte[1] .......byte[30]
# assume background in BLASK color
def prt_f24_string(xx, yy, f24_string, ch_front_color, ch_back_color):
    global char_font_size
    global char_byte_of_row
    a = " "
    f_xx = xx
    for f24 in (f24_string):
        f_pos = Clk_font_map.find(f24)*72
        ch_array = font_clk._FONT[f_pos:f_pos+72]
        byte_no = 0
        for y_pos in range(char_font_size):
            for ch_char in range(char_byte_of_row):
                a = ch_array[byte_no]
                for x_pos in range(8):
                    b = (a & 128)/128
                    if b == 0:
                        TFT.pixel( ch_char*8+x_pos+f_xx, y_pos+yy, ch_back_color )
                    else:
                        TFT.pixel( ch_char*8+x_pos+f_xx, y_pos+yy, ch_front_color )
                    a = a << 1
                byte_no += 1
        f_xx += 24

#===========
TFT.fill(df_GREEN)
TFT.text(font3, "Display OK.", 25, 35, df_MAGENTA)
TFT.text(font3, "WIFI connecting...", 25, 67, df_MAGENTA)

# Router credentials
ssid = "ssid"   # wifi router name
pw = "password" # wifi router password
print("Connecting to wifi...")

#start watchdog
wdt = WDT(timeout=8300)

# wifi connection
wifi = network.WLAN(network.STA_IF) # station mode
wifi.active(True)
wifi.connect(ssid, pw)

# wait for connection
while not wifi.isconnected():
    pass

wdt.feed()
# wifi connected
print("Connected. IP: ",str(wifi.ifconfig()[0], "\n")) 

rtc = machine.RTC()
rtc.datetime((2000, 1, 1, 0, 0, 0, 00, 0))
wdt.feed()
ntptime.settime()
wdt.feed()
time.sleep(2)

utc_shift = 8               # define time zone
# utime.mktime(tt) is time format convert to second format
tm = utime.localtime(utime.mktime(utime.localtime()) + utc_shift*3600)
# tm = (year, month, day, hour, minute, second, week, ss)
# change sequence to store into rtc
# tm = (year, month, day, 0, hour, minute, second, 0)
print("utime.localtime  --> ", tm)
tm = tm[0:3] + (0,) + tm[3:6] + (0,)

wdt.feed()
rtc.datetime(tm)
print("rtc.datetime    --> ", rtc.datetime())
print("time.localtime  --> ", time.localtime())
print("Read time.localtime()[n] value for clock operation")

def dec_to_2str(number):
    return str(number +100)[1:3]

def dec_to_2dig(number):
    return number//10, number%10

f_YELLOW = b'\xFF\xE0'
ary_size = 74*135*2
#show big digit num onto TFT
def put_buf(pos_x, pox_y, prt_num, f_color):
    global ary_size
    global pos
    global f_YELLOW
    color_byte = (f_color).to_bytes(2, 'big')
    tmp_ary = bytearray(ary_size)
    fo = open("/font/tube"+str(prt_num)+"_74x135.raw", "rb")
    #print("Information of checking RAW file :-")
    p_buf = fo.read(ary_size)
    if f_color != df_YELLOW :
        for ct in range(0, ary_size,2):
            tmp_ary[ct] = p_buf[ct]
            tmp_ary[ct+1] = p_buf[ct+1]
            if tmp_ary[ct:ct+2] == f_YELLOW:
                tmp_ary[ct] = color_byte[0]
                tmp_ary[ct+1] = color_byte[1]
    else:
        tmp_ary = p_buf
    TFT.blit_buffer(tmp_ary, pos_x, pox_y, 74, 135)
    fo.close()

def get_Lunar():
    TFT.text(font3, "Get   L", 9, 80, df_RED, df_BLACK)
    year  = str(time.localtime()[0])
    month = dec_to_2str(time.localtime()[1])
    day   = dec_to_2str(time.localtime()[2])

    r = urequests.get("https://www.iamwawa.cn/nongli/api/?type=solar&year="+year+"&month="+month+"&day="+day)
    wdt.feed()
    json_data = r.json()
    wdt.feed()
    print("List of variable (Lunar):-")
    for i in (json_data):
        print (i)
    Lunar_return = json_data['status']
    print("Lunar_status :- ", Lunar_return)
    wdt.feed()
    if json_data['status']:
        Lunar_year = json_data['data']['ganzhi']
        Lunar_day  = json_data['data']['lunar_date']
        print("Lunar_year :- ", Lunar_year)
        prt_f24_string(0, 164, Lunar_year, st7789.WHITE, st7789.BLACK)
        print("Lunar_day  :- ", Lunar_day)
        prt_f24_string(88, 164, Lunar_day, st7789.WHITE, st7789.BLACK)
    else:
        clear_space = '\u9999\u9999'
        prt_f24_string( 0, 164, clear_space, st7789.WHITE, st7789.BLACK)
        prt_f24_string(88, 164, clear_space, st7789.WHITE, st7789.BLACK)
    wdt.feed()
    r.close()    

def get_T_H():
    TFT.text(font3, "Get   T", 9, 80, df_GREEN, df_BLACK)
    r = urequests.get("https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=rhrread&lang=en")
    wdt.feed()

    json_data = r.json()
    wdt.feed()

    T_set = json_data['temperature']['data']
    for i in range(len(T_set)):
        #print(i)
        T_pla = json_data['temperature']['data'][i]['place']
        T_val = json_data['temperature']['data'][i]['value']
        #print(i, T_pla, T_val)
        if T_pla == 'Tuen Mun':
            t_value = T_val

    #print("\n\nTuen Mun is at ",t_value, "C")
    #print("\n\nData of humidity:-")

    H_val = json_data['humidity']['data'][0]['value']
    #print("Humidity is at ",H_val, "%")

    wdt.feed()
    r.close()
    return t_value, H_val

solar24_ss = [["小寒", 1736073060],\
["大寒", 1737345600],\
["立春", 1738620600],\
["雨水", 1739901900],\
["驚蟄", 1741190640],\
["春分", 1742489820],\
["清明", 1743799320],\
["谷雨", 1745120820],\
["立夏", 1746452880],\
["小滿", 1747795440],\
["芒種", 1749145620],\
["夏至", 1750501980],\
["小暑", 1751860620],\
["大暑", 1753219380],\
["立秋", 1754574360],\
["處暑", 1755923460],\
["白露", 1757263740],\
["秋分", 1758593940],\
["寒露", 1759912740],\
["霜降", 1761220260],\
["立冬", 1762516980],\
["小雪", 1763804160],\
["大雪", 1765083900],\
["冬至", 1766358240],\
["小寒", 1767630240],\
["大寒", 1768902360],\
["立春", 1770177780],\
["雨水", 1771458660],\
["驚蟄", 1772747880],\
["春分", 1774046460],\
["清明", 1775356500],\
["谷雨", 1776677460],\
["立夏", 1778010060],\
["小滿", 1779352080],\
["芒種", 1780702800],\
["夏至", 1782058560],\
["小暑", 1783417800],\
["大暑", 1784776020],\
["立秋", 1786131480],\
["處暑", 1787480160],\
["白露", 1788820860],\
["秋分", 1790150640],\
["寒露", 1791469860],\
["霜降", 1792777080],\
["立冬", 1794074040],\
["小雪", 1795361040],\
["大雪", 1796640900],\
["冬至", 1797915180],\
["小寒", 1799187240],\
["大寒", 1800459360],\
["立春", 1801734720],\
["雨水", 1803015660],\
["驚蟄", 1804304700],\
["春分", 1805603520],\
["清明", 1806913320],\
["谷雨", 1808234580],\
["立夏", 1809566760],\
["小滿", 1810909200],\
["芒種", 1812259440],\
["夏至", 1813615680],\
["小暑", 1814974380],\
["大暑", 1816333200],\
["立秋", 1817688120],\
["處暑", 1819037340],\
["白露", 1820377440],\
["秋分", 1821707880],\
["寒露", 1823026500],\
["霜降", 1824334320],\
["立冬", 1825630740],\
["小雪", 1826918280],\
["大雪", 1828197600],\
["冬至", 1829472360],\
["小寒", 1830744000],\
["大寒", 1832016480],\
["立春", 1833291540],\
["雨水", 1834572780],\
["驚蟄", 1835861520],\
["春分", 1837160580],\
["清明", 1838470140],\
["谷雨", 1839791520],\
["立夏", 1841123640],\
["小滿", 1842466080],\
["芒種", 1843816380],\
["夏至", 1845172500],\
["小暑", 1846531380],\
["大暑", 1847889960],\
["立秋", 1849245120],\
["處暑", 1850594040],\
["白露", 1851934500],\
["秋分", 1853264580],\
["寒露", 1854583620],\
["霜降", 1855891020],\
["立冬", 1857187920],\
["小雪", 1858474980],\
["大雪", 1859754840],\
["冬至", 1861029060],\
["小寒", 1862301240],\
["大寒", 1863573180],\
["立春", 1864848780],\
["雨水", 1866129480],\
["驚蟄", 1867418760],\
["春分", 1868717280],\
["清明", 1870027320],\
["谷雨", 1871348220],\
["立夏", 1872680760],\
["小滿", 1874022720],\
["芒種", 1875373440],\
["夏至", 1876729260],\
["小暑", 1878088380],\
["大暑", 1879446720],\
["立秋", 1880802120],\
["處暑", 1882150860],\
["白露", 1883491440],\
["秋分", 1884821460],\
["寒露", 1886140500],\
["霜降", 1887447960],\
["立冬", 1888744800],\
["小雪", 1890032040],\
["大雪", 1891311720],\
["冬至", 1892586180],\
["小寒", 1893858060],\
["大寒", 1895130360],\
["立春", 1896405540],\
["雨水", 1897686660],\
["驚蟄", 1898975460],\
["春分", 1900274460],\
["清明", 1901583960],\
["谷雨", 1902905400],\
["立夏", 1904237400],\
["小滿", 1905579900],\
["芒種", 1906930020],\
["夏至", 1908286380],\
["小暑", 1909644960],\
["大暑", 1911003840],\
["立秋", 1912358700],\
["處暑", 1913707980],\
["白露", 1915048140],\
["秋分", 1916378580],\
["寒露", 1917697260],\
["霜降", 1919005080],\
["立冬", 1920301560],\
["小雪", 1921589100],\
["大雪", 1922868540],\
["冬至", 1924143240],\
["小寒", 1925415000],\
["大寒", 1926687360],\
["立春", 1927962480],\
["雨水", 1929243600],\
["驚蟄", 1930532520],\
["春分", 1931831340],\
["清明", 1933141020],\
["谷雨", 1934462160],\
["立夏", 1935794460],\
["小滿", 1937136660],\
["芒種", 1938487140],\
["夏至", 1939843080],\
["小暑", 1941202080],\
["大暑", 1942560480],\
["立秋", 1943915880],\
["處暑", 1945264620],\
["白露", 1946605320],\
["秋分", 1947935220],\
["寒露", 1949254440],\
["霜降", 1950561720],\
["立冬", 1951858800],\
["小雪", 1953145800],\
["大雪", 1954425780],\
["冬至", 1955699940],\
["小寒", 1956972240],\
["大寒", 1958244120],\
["立春", 1959519660],\
["雨水", 1960800360],\
["驚蟄", 1962089640],\
["春分", 1963388100],\
["清明", 1964698080],\
["谷雨", 1966018980],\
["立夏", 1967351460],\
["小滿", 1968693480],\
["芒種", 1970044020],\
["夏至", 1971399960],\
["小暑", 1972758900],\
["大暑", 1974117420],\
["立秋", 1975472640],\
["處暑", 1976821620],\
["白露", 1978162080],\
["秋分", 1979492280],\
["寒露", 1980811200],\
["霜降", 1982118900],\
["立冬", 1983415560],\
["小雪", 1984702980],\
["大雪", 1985982480],\
["冬至", 1987257180],\
["小寒", 1988528940],\
["大寒", 1989801360],\
["立春", 1991076360],\
["雨水", 1992357600],\
["驚蟄", 1993646280],\
["春分", 1994945340],\
["清明", 1996254720],\
["谷雨", 1997576160],\
["立夏", 1998908100],\
["小滿", 2000250600],\
["芒種", 2001600660],\
["夏至", 2002957020],\
["小暑", 2004315600],\
["大暑", 2005674420],\
["立秋", 2007029400],\
["處暑", 2008378620],\
["白露", 2009718840],\
["秋分", 2011049280],\
["寒露", 2012368080],\
["霜降", 2013675840],\
["立冬", 2014972500],\
["小雪", 2016259920],\
["大雪", 2017539540],\
["冬至", 2018814060],\
["小寒", 2020086000],\
["大寒", 2021358180],\
["立春", 2022633480],\
["雨水", 2023914360],\
["驚蟄", 2025203460],\
["春分", 2026502040],\
["清明", 2027811900],\
["谷雨", 2029132860],\
["立夏", 2030465280],\
["小滿", 2031807240],\
["芒種", 2033157840],\
["夏至", 2034513600],\
["小暑", 2035872780],\
["大暑", 2037231060],\
["立秋", 2038586520],\
["處暑", 2039935260],\
["白露", 2041276020],\
["秋分", 2042605920],\
["寒露", 2043925260],\
["霜降", 2045232540],\
["立冬", 2046529620],\
["小雪", 2047816680],\
["大雪", 2049096660],\
["冬至", 2050370940],\
["小寒", 2051643120],\
["大寒", 2052915060],\
["立春", 2054190540],\
["雨水", 2055471300],\
["驚蟄", 2056760400],\
["春分", 2058059040],\
["清明", 2059368780],\
["谷雨", 2060689860],\
["立夏", 2062022040],\
["小滿", 2063364240],\
["芒種", 2064714540],\
["夏至", 2066070660],\
["小暑", 2067429420],\
["大暑", 2068788120],\
["立秋", 2070143160],\
["處暑", 2071492380],\
["白露", 2072832660],\
["秋分", 2074163100],\
["寒露", 2075481900],\
["霜降", 2076789780],\
["立冬", 2078086320],\
["小雪", 2079373920],\
["大雪", 2080653360],\
["冬至", 2081928180]]
def get_solar24():
    ct = 0
    today_ss = utime.mktime(utime.localtime())
    while today_ss > solar24_ss[ct][1] :
        ct +=1
    s1 = utime.localtime(solar24_ss[ct-1][1])
    s2 = utime.localtime(solar24_ss[ct][1])
    #(year, month, day, hour, minute, second, week, ss)
    date1 = str(s1[0])+"/"+str(s1[1])+"/"+str(s1[2])+"-"+str(s1[3])+":"+str(s1[4])
    date2 = str(s2[0])+"/"+str(s2[1])+"/"+str(s2[2])+"-"+str(s2[3])+":"+str(s2[4])
    return ct, date1, date2

#day_of_week = ["Monday","Tuesday","Wednesday",
#               "Thursday","Friday","Saturday","Sunday"];
TFT.fill(df_BLACK)

last_hms=[99,99,99,99,99,99]
while True:
    year  = str(time.localtime()[0])
    month = dec_to_2str(time.localtime()[1])
    day   = dec_to_2str(time.localtime()[2])
    week_day = time.localtime()[6]+1
    if week_day == 7:
        week_day = 15
    hour1,   hour0   = dec_to_2dig(time.localtime()[3])
    min1 ,   min0    = dec_to_2dig(time.localtime()[4])
    second = str(time.localtime()[5]+100)[1:3]
    
    wdt.feed()
    if last_hms[3] != min0:
        put_buf(3+160, 3, min1, df_color[exit_col_code])
        put_buf(3+240, 3, min0, df_color[exit_col_code])
        exit_col_code = (exit_col_code + 1)%total_col
        last_hms[3] = min0

    wdt.feed()
    #Do every 10 hour
    if last_hms[0] != hour1:
        TFT.text(font3, day+"/"+month+"/"+year,  0, 138, df_RED)

        str_week_day = "星期"+Clk_font_map[week_day]
        prt_f24_string(185, 140, str_week_day, df_YELLOW, df_BLACK)

        get_Lunar()
        last_hms[0] = hour1
        
        year_gas, gas_date1, gas_date2 = get_solar24()
        prt_f24_string(0, 164+24, solar24_ss[year_gas-1][0], df_YELLOW, df_BLUE)
        prt_f24_string(0, 164+48, solar24_ss[year_gas][0], df_YELLOW, df_BLUE)
        TFT.text(font2, gas_date1,  50, 164+24+8, df_CYAN)
        TFT.text(font2, gas_date2,  50, 164+48+8, df_FOREST)
    
    #Do every hour
    if last_hms[1] != hour0:
        Temp , Hum = get_T_H()
        print ("Temp-%2d C  , Hum-%2d pcent" % (Temp, Hum))
        #last_hms[2] = min1
        last_hms[1] = hour0
        TFT.text(font3, dec_to_2str(Temp)+"C",  205, 166, df_MAGENTA)
        TFT.text(font3, dec_to_2str(Hum)+"%" ,  265, 166, df_GREEN)
        put_buf(3,     3, hour1, df_ORANGE)
        put_buf(3+80,  3, hour0, df_ORANGE)

    wdt.feed()
    TFT.text(font3, second,  275, 138, df_WHITE)
