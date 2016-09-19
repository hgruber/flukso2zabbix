#!/bin/python

import requests
import datetime
import re
import json
import paho.mqtt.client as mqtt
from zabbix.sender import ZabbixMetric, ZabbixSender

flukso_host = 'flukso'
zabbix_host = 'zabbix'
user        = 'root'
password    = 'passwd'
application = 'flukso'

sid = ''
rsd = re.compile('^/sensor/([0-9a-f]*)/(.*)$')
all_sensors = {}

def auth():
    global flukso_host, user, password
    url  = 'http://' + flukso_host + '/cgi-bin/luci/rpc/auth'
    data = {
        'method': 'login',
        'params': [ user, password ],
        'id': datetime.datetime.now().strftime('%s')
    }
    r = requests.post(url, data=json.dumps(data))
    response = json.loads(r.content)
    if 'error' in response and response['error'] == None and 'result' in response: return response['result']
    else: return False

def info(session):
    global flukso_host, user, password
    url  = 'http://' + flukso_host + '/cgi-bin/luci/rpc/uci?auth=' + session
    data = {
        'method': 'get_all',
        'params': [ 'flukso' ],
        'id': datetime.datetime.now().strftime('%s')
    }
    r = requests.post(url, data=json.dumps(data))
    try:
        response = json.loads(r.content)
    except:
        return False
    else:
        if 'error' in response and response['error'] == None and 'result' in response: return response['result']
        else: return False

def get_sensors():
    global sid, all_sensors
    if sid == '':
        sid = auth()
    if not sid:
        print 'Authentication failed.'
        return False
    flukso = info(sid)
    if not flukso:
        sid = auth()
        flukso = info(sid)
    if not flukso:
        print 'Authentication failed.'
        return False
    sensors = {}
    for sensor in flukso:
        if 'function' in flukso[sensor]:
            name = flukso[sensor]['function']
            sensor_type = flukso[sensor]['type']
            all_sensors[flukso[sensor]['id']] = { 'name': name, 'type': sensor_type }
            if sensor_type not in sensors: sensors[sensor_type] = []
            sensors[sensor_type].append({ '{#SENSOR}': name })
            print 'found sensor: ', name
    message = []
    for sensor_type in sensors:
        data = {}
        data['data'] = sensors[sensor_type]
        message.append(ZabbixMetric(zabbix_host, application+'.discovery.' + sensor_type, json.dumps(data)))
    print 'sending sensor items to zabbix server: ' + zabbix_host
    ZabbixSender(zabbix_host, 10051).send(message)


def on_connect(client, userdata, flags, rc):
    print 'connected to mosquitto-server at: ' + flukso_host
    client.subscribe("/#")

def on_message(client, userdata, msg):
    sensor_id = rsd.sub('\\1', msg.topic)
    sensor_rd = rsd.sub('\\2', msg.topic)
    if sensor_id in all_sensors:
        typ  = all_sensors[sensor_id]['type']
        name = all_sensors[sensor_id]['name']
    else:
        get_sensors()
        return
    try:
        values = json.loads(msg.payload)
    except ValueError as err:
        print(err)
        return
    parameter = application + '.' + typ + '.' + sensor_rd + '[' + name + ']'
    message = []
    message.append(ZabbixMetric(zabbix_host, parameter, values[1]))
    ZabbixSender(zabbix_host, 10051).send(message)
    
get_sensors()

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(flukso_host, 1883, 60)
client.loop_forever()
