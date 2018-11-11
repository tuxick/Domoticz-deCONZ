#!/usr/bin/env python3
# coding: utf-8 -*-

import Domoticz

#****************************************************************************************************
# Global fonctions

def rgb_to_xy(rgb):
	''' convert rgb tuple to xy tuple '''
	red, green, blue = rgb
	r = ((red + 0.055) / (1.0 + 0.055))**2.4 if (red > 0.04045) else (red / 12.92)
	g = ((green + 0.055) / (1.0 + 0.055))**2.4 if (green > 0.04045) else (green / 12.92)
	b = ((blue + 0.055) / (1.0 + 0.055))**2.4 if (blue > 0.04045) else (blue / 12.92)
	X = r * 0.664511 + g * 0.154324 + b * 0.162028
	Y = r * 0.283881 + g * 0.668433 + b * 0.047685
	Z = r * 0.000088 + g * 0.072310 + b * 0.986039
	cx = 0
	cy = 0
	if (X + Y + Z) != 0:
		cx = X / (X + Y + Z)
		cy = Y / (X + Y + Z)
	return (cx, cy)

def rgb_to_hsl(rgb):
	''' convert rgb tuple to hls tuple '''
	r, g, b = rgb
	r = float(r/255)
	g = float(g/255)
	b = float(b/255)
	high = max(r, g, b)
	low = min(r, g, b)
	h, s, l = ((high + low) / 2,)*3

	if high == low:
		h = 0.0
		s = 0.0
	else:
		d = high - low
		s = d / (2 - high - low) if l > 0.5 else d / (high + low)
		h = {
			r: (g - b) / d + (6 if g < b else 0),
			g: (b - r) / d + 2,
			b: (r - g) / d + 4,
		}[high]
		h /= 6

	return h, s, l
	
def xy_to_rgb(x, y, brightness = 1):
	
	x = float(x)
	y = float(y)
	z = 1.0 - x - y;
	
	Y = brightness
	X = (Y / y) * x
	Z = (Y / y) * z
	
	r =  X * 1.656492 - Y * 0.354851 - Z * 0.255038;
	g = -X * 0.707196 + Y * 1.655397 + Z * 0.036152;
	b =  X * 0.051713 - Y * 0.121364 + Z * 1.011530;
  
	r = 12.92 * r if r <= 0.0031308 else (1.0 + 0.055) * pow(r, (1.0 / 2.4)) - 0.055
	g = 12.92 * g if g <= 0.0031308 else (1.0 + 0.055) * pow(g, (1.0 / 2.4)) - 0.055
	b = 12.92 * b if b <= 0.0031308 else (1.0 + 0.055) * pow(b, (1.0 / 2.4)) - 0.055

	if (r > b) and (r > g):
		if (r > 1.0):
			g = g / r
			b = b / r
			r = 1.0

	elif (g > b) and (g > r):
		if (g > 1.0):
			r = r / g
			b = b / g
			g = 1.0

	elif (b > r) and (b > g):
		if (b > 1.0):
			r = r / b
			g = g / b
			b = 1.0

	return {'r': int(r * 255), 'g': int(g * 255), 'b': int(b * 255)}
	
	
#**************************************************************************************************
# Domoticz fonctions

CubeEvent = {'7000':'wake'}
#https://github.com/dresden-elektronik/deconz-rest-plugin/wiki/Supported-Devices

def ReturnUpdateValue(command,val):

	val = str(val)
	command = str(command)
	
	kwarg = {}
	
	#operator
	if command == 'on':
		if val == 'True':
			kwarg['nValue'] = 1
			kwarg['sValue'] = 'on'
		else:
			kwarg['nValue'] = 0
			kwarg['sValue'] = 'off'
			
	if command == 'bri':
		kwarg['nValue'] = 1
		val = int(int(val) * 100 / 255 )
		kwarg['sValue'] = str(val)
		
	if command == 'xy':
		x,y = eval(str(val))
		rgb = xy_to_rgb(x,y,1)
		kwarg['nValue'] = 1
		#kwarg['sValue'] = str(255)
		kwarg['Color'] = '{"b":' + str(rgb['b']) + ',"cw":0,"g":' + str(rgb['g']) + ',"m":3,"r":' + str(rgb['r']) + ',"t":0,"ww":0}'
		
	if command == 'all_on' or command == 'any_on':
		if val == 'True':
			kwarg['nValue'] = 1
			kwarg['sValue'] = 'on'
		else:
			kwarg['nValue'] = 0
			kwarg['sValue'] = 'off'
		
	#sensor
	if command == 'open':
		if val == 'True':
			kwarg['nValue'] = 1
			kwarg['sValue'] = 'Open'
		else:
			kwarg['nValue'] = 0
			kwarg['sValue'] = 'Closed'
	
	if command == 'temperature':
		kwarg['nValue'] = 0
		val = round( int(val) / 100 , 2  )
		kwarg['sValue'] = str(val)
		
	if command == 'pressure':
		kwarg['nValue'] = 0
		kwarg['sValue'] = str(val)
		
	if command == 'humidity':
		val = int( int(val) / 100)
		kwarg['nValue'] = val
		kwarg['sValue'] = '0'
		
	if command == 'lux':
		kwarg['nValue'] = 0
		kwarg['sValue'] = str(val)

	if command == 'presence':
		if val == 'True':
			kwarg['nValue'] = 1
			kwarg['sValue'] = 'On'
		else:
			kwarg['nValue'] = 0
			kwarg['sValue'] = 'Off'
			
	#switch
	if command == 'buttonevent':
		kwarg['nValue'] = int(val)
		kwarg['sValue'] = str(val)

	# other
	if command == 'battery':
		if not val.isdigit():
			kwarg['BatteryLevel'] = 255
		else:
			kwarg['BatteryLevel'] = int( int(val) * 255 / 100 ) - 5

	if command == 'xxxx':
		kwarg['SignalLevel'] = 100

	#if command == 'lastupdated':
	#    kwarg['LastUpdate'] = val.replace('T',' ')

	return kwarg

#https://github.com/dresden-elektronik/deconz-rest-plugin/issues/138
def ButtonconvertionXCUBE_R(val):
	kwarg = {}
	if int(val) < 0:
		kwarg['nValue'] = 10
	else:
		kwarg['nValue'] = 20
	kwarg['sValue'] = str( kwarg['nValue'] )
	return kwarg
		
def ButtonconvertionXCUBE(val):
	kwarg = {}
	val = str(val)
	if val == '7007':#shake
		kwarg['nValue'] = 10
	elif val == '7000': #wake
		kwarg['nValue'] = 20
	elif val == '7008':#drop
		kwarg['nValue'] = 30
	elif int(val[3]) == (7 - int(val[0])) :#180 flip
		kwarg['nValue'] = 50
	elif val[1:] == '000':#push
		kwarg['nValue'] = 60
	elif val[0] == val[3]:#double tap
		kwarg['nValue'] = 70
	else:#90 flip
		kwarg['nValue'] = 40
	kwarg['sValue'] = str( kwarg['nValue'] )
	return kwarg
