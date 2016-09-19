from python:2.7-alpine

RUN pip install py-zabbix paho-mqtt requests
ADD flukso2zabbix.py /flukso2zabbix.py
ENTRYPOINT ["python", "/flukso2zabbix.py"]
