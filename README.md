# flukso2zabbix
push flukso readings to zabbix

This tiny python script is run as a permanent service. It connects to the mosquitto server run on the flukso. All sensor readings are passed on to a zabbix server. If devices were unknown to zabbix the flukso will be queried and all devices will be discovered automatically by low level discovery rules.
This way you will get timeseries for all readings from your flukso in zabbix.
