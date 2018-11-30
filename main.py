import requests
import json
import threading
import time
import pandas as pd
import mysql.connector
import re
import atexit
from datetime import timedelta, datetime

def cleanDB(cnx):
    print("Fechando a conexao")
    cnx.close()

def virtualMetricsDB(virtualMetrics, cnx, agent, sliceID, count, timestamp):
    i = 0
    j = 0

    if count != 0:
        cursor = cnx.cursor()
        select = 'SELECT physical_server_id FROM Physical_server WHERE ip="' + str(agent) + '" AND slice_id="' + str(sliceID) + '"'
        cursor.execute(select)
        print("COUNT: ", count)

        for (physical_server_id) in cursor:
            serverID = physical_server_id
            serverID = re.sub('\W+','', str(serverID))

            for i in range(len(virtualMetrics[0]['data']['result'])):
                addVirtualServer = 'INSERT INTO `Virtual_resource` (`name`, `physical_server_id`) VALUES("' + str(virtualMetrics[0]['data']['result'][i]['metric']['name']) + '", "' + str(serverID) + '")'
                print(addVirtualServer)
                cursor.execute(addVirtualServer)


    cursor = cnx.cursor()
    select = 'SELECT virtual_resource_id, name FROM Slice NATURAL JOIN Physical_server NATURAL JOIN Virtual_resource WHERE slice_id="'+ str(sliceID) + '"' + 'AND ip="' + str(agent) + '"'
    cursor.execute(select)

    i = 0
    nMetrics = 6 # Número de métricas coletadas!

    j = 0
    metricDict = dict()

    #timestamp = virtualMetrics[0]['data']['result'][0]['value'][0]
    #timestamp = time.ctime(int(timestamp))
    print("Timestamp %s \n" % timestamp)

    for (virtual_resource_id, name) in cursor:
        virtualResource = virtual_resource_id
        virtualResource = re.sub('\W+', '', str(virtualResource))
        metricDict[name] = [virtualResource, timestamp]

    i = 0
    j = 0
    for i in range(nMetrics):
        for j in range(len(virtualMetrics[i]['data']['result'])):
                print("j ", str(virtualMetrics[i]['data']['result'][j]['value'][1]), "for name: ", str(virtualMetrics[i]['data']['result'][j]['metric']['name']) )
                metricDict[str(virtualMetrics[i]['data']['result'][j]['metric']['name'])].append(str(virtualMetrics[i]['data']['result'][j]['value'][1]))

    for slice,val in metricDict.items():
        print(slice, "-> ", val)

    i = 0
    for key, value in metricDict.items():
        if(len(value) == 8):
            addMetric = 'INSERT INTO `Virtual_resource_measure` (`virtual_resource_id`, `timestamp`, `net_received`, `net_transmited`, `cpu_usage`, `ram_usage`, `disk_reads`, `disk_writes`) VALUES("' + str(value[0]) + '", "' + str(value[1]) + '", "' + str(value[2]) + '", "' + str(value[3]) + '", "' + str(value[4]) + '", "' + str(value[5]) + '", "' + str(value[6]) + '", "' + str(value[7]) + '")'
            print("Add Metrics ", addMetric)
            try:
                cursor.execute(addMetric)
            except:
                print("Error on Insert Metric ", value)
        else:
            print("Metrics not collected right!")

    cnx.commit()


class sliceThread (threading.Thread):
    def __init__(self, sliceID, agents, cnx):
        threading.Thread.__init__(self)
        self.sliceID = sliceID
        self.agents = agents
        self.cnx = cnx
        print(sliceID, agents)

    def run(self):
        count = len(self.agents)
        while (True):

            print("Starting Collecting Metrics from {} Agents: {}\n".format(self.sliceID,self.agents))

            for i in self.agents:
                URL = "http://%s:9090/api/v1/query?" % i
                print(URL)


                # Métrica 1: Virtual network receive
                query = 'sum(rate(container_network_receive_bytes_total{name=~"%s.*"}[10s])) by (name)' % self.sliceID
                timestamp = datetime.now().timestamp()
                PARAMS = {'query': query, 'time': timestamp}
                print("Timestamp ", timestamp)
                request = requests.get(url = URL, params = PARAMS)
                metricV1 = json.loads(request.text)
                print("Métrica 1: %s\n" % metricV1)


                #Métrica 2: Virtual network transmit
                query = 'sum(rate(container_network_transmit_bytes_total{name=~"%s.*"}[10s])) by (name)' % self.sliceID
                PARAMS = {'query': query, 'time': timestamp}

                request = requests.get(url = URL, params = PARAMS)
                metricV2 = json.loads(request.text)
                print("Métrica 2: %s\n" % metricV2)

                #Métrica 3: Virtual CPU
                #query = 'sum(rate(container_cpu_usage_seconds_total{name=~"%s.*"}[10s])) by (name) * 100' % self.sliceID
                query = 'sum(container_memory_rss{name=~"%s.*"}) by (name)' % self.sliceID
                PARAMS = {'query': query, 'time': timestamp}

                request = requests.get(url = URL, params = PARAMS)
                metricV3 = json.loads(request.text)
                print("Métrica 3: %s\n" % metricV3)

                #Métrica 4: Virtual RAM
                query = 'container_memory_usage_bytes{name=~"%s.*"}' % self.sliceID
                PARAMS = {'query': query, 'time': timestamp}

                request = requests.get(url = URL, params = PARAMS)
                metricV4 = json.loads(request.text)
                print("Métrica 4: %s\n" % metricV4)

                #Métrica 5: Virtual Disk Bytes Reads
                query = 'container_fs_reads_bytes_total{name=~"%s.*"}' % self.sliceID
                PARAMS = {'query': query, 'time': timestamp}

                request = requests.get(url = URL, params = PARAMS)
                metricV5 = json.loads(request.text)
                print("Métrica 5: %s\n" % metricV5)

                #Métrica 6: Virtual Disk Bytes Writes
                query = 'container_fs_writes_bytes_total{name=~"%s.*"}' % self.sliceID
                PARAMS = {'query': query, 'time': timestamp}

                request = requests.get(url = URL, params=PARAMS)
                metricV6 = json.loads(request.text)
                print("Métrica 6: %s\n" % metricV6)

                virtualMetrics = [metricV1, metricV2, metricV3, metricV4, metricV5, metricV6]

                #Métricas Físicas
                #Métrica 1: Physical Network receive
                #query = 'sum(rate(container_network_receive_bytes_total{id="/"}[10s])) by (id)'
                #PARAMS = {'query': query, 'time': timestamp}
                #request = requests.get(url = URL, params = PARAMS)
                #metricP1 = json.loads(request.text)
                #print("Métrica P1: %s" % metricP1)

                #Métrica 2: Physical Network transmit
                #query = 'sum(rate(container_network_transmit_bytes_total{id="/"}[10s])) by (id)'
                #PARAMS = {'query': query, 'time': timestamp}

                #request = requests.get(url=URL, params=PARAMS)
                #metricP2 = json.loads(request.text)
                #print("Métrica P2: %s" % metricP2)

                #Métrica 3: Physical CPU
                #query = 'sum(sum by (container_name)( rate(container_cpu_usage_seconds_total[10s] ) )) / count(node_cpu_seconds_total{mode="system"}) * 100'
                #PARAMS = {'query': query, 'time': timestamp}

                #request = requests.get(url=URL, params=PARAMS)
                #metricP3 = json.loads(request.text)
                #print("Métrica P3: %s" % metricP3)

                #Métrica 4: Physical RAM
                #query = 'sum(node_memory_MemTotal_bytes) - sum(node_memory_MemAvailable_bytes)'
                #PARAMS = {'query': query, 'time': timestamp}

                #request = requests.get(url=URL, params=PARAMS)
                #metricP4 = json.loads(request.text)
                #print("Métrica P4: %s" % metricP4)

                #physicalMetrics = [metricP1, metricP2, metricP3, metricP4]
                virtualMetricsDB(virtualMetrics, self.cnx, i, self.sliceID, count, timestamp)

                if count != 0:
                    count = count - 1

                #Métrica 5: Physical Disk Bytes Reads
                #query = 'sum(rate(node_disk_bytes_read_total[10s])) by (device)'
                #PARAMS = {'query': query, 'time': timestamp}

                #request = requests.get(url=URL, params=PARAMS)
                #metricP5 = json.loads(request.text)
                #print("Métrica P5: %s" % metricP5)

                #Métrica 6: Physical Disk Bytes Writes
                #query = 'sum(rate(node_disk_bytes_written_total[10s])) by (device)'
                #PARAMS = {'query': query, 'time': timestamp}

                #request = requests.get(url=URL, params=PARAMS)
                #metricP6 = json.loads(request.text)
                #print("Métrica P6: %s" % metricP6)

            time.sleep(30)





agentsList = ['slice1', ['200.136.191.111','200.136.191.94'], 'slice2', ['200.136.191.101','200.136.191.24']]
#for key, value in agentsList.items():

cnx = mysql.connector.connect(user="andre", password="openstack",
                                          host="localhost",
                                          database="leris_db")
cnx2 = mysql.connector.connect(user="andre", password="openstack",
                                          host="localhost",
                                          database="leris_db")

cursor = cnx.cursor()
i = 0

while i < len(agentsList):
    addSlice = 'INSERT INTO `Slice` (`slice_id`) VALUES("' + str(agentsList[i]) + '")'
    cursor.execute(addSlice)
    cnx.commit()
    j = 0
    while j < len(agentsList[i+1]):
        addPhysicalServer = 'INSERT INTO `Physical_server` (`ip`, `slice_id`) VALUES("' + str(agentsList[i+1][j]) + '", "' + str(agentsList[i]) + '")'
        print(addPhysicalServer)
        cursor.execute(addPhysicalServer)
        cnx.commit()
        j = j + 1
    i = i + 2

try:
    threadSlice1 = sliceThread(agentsList[0], agentsList[1], cnx)
    threadSlice1.start()
except:
    print ("Caught exception in Thread 1")

try:
    threadSlice2 = sliceThread(agentsList[2], agentsList[3], cnx2)
    threadSlice2.start()
except:
    print("Caught exception in Thread 2")

atexit.register(cleanDB, cnx)
atexit.register(cleanDB, cnx2)








