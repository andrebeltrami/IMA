import requests
import json
import threading
import time
import pandas as pd
import mysql.connector
import re


def virtualMetricsDB(virtualMetrics, cnx, agent, sliceID):
    i = 0
    j = 0

    cursor = cnx.cursor()
    select = 'SELECT physical_server_id FROM Physical_server WHERE ip="' + str(agent) + '" AND slice_id="' + str(sliceID) + '"'
    cursor.execute(select)

    for (physical_server_id) in cursor:
        serverID = physical_server_id

    serverID = re.sub('\W+','', str(serverID))

    for i in range(len(virtualMetrics[0]['data']['result'])):
        addVirtualServer = 'INSERT INTO `Virtual_resource` (`name`, `physical_server_id`) VALUES("' + str(
            virtualMetrics[0]['data']['result'][i]['metric']['name']) + '", "' + str(serverID) + '")'
        print(addVirtualServer)
        cursor.execute(addVirtualServer)

    cnx.commit()


class sliceThread (threading.Thread):
    def __init__(self, sliceID, agents, cnx):
        threading.Thread.__init__(self)
        self.sliceID = sliceID
        self.agents = agents
        self.cnx = cnx
        print(sliceID, agents)

    def run(self):
        while (True):

            print("Starting Collecting Metrics from {} Agents: {}\n".format(self.sliceID,self.agents))

            for i in self.agents:
                URL = "http://%s:9090/api/v1/query?" % i
                #print(URL)

                # Métrica 1: Virtual network receive
                query = 'sum(rate(container_network_receive_bytes_total{name=~"%s.*"}[10s])) by (name)' % self.sliceID
                PARAMS = {'query': query}
                request = requests.get(url = URL, params = PARAMS)
                metricV1 = json.loads(request.text)
                print(len(metricV1['data']['result']))
                timestamp = metricV1['data']['result'][0]['value'][0]
                print("Métrica 1: %s\n" % metricV1)


                #Métrica 2: Virtual network transmit
                query = 'sum(rate(container_network_transmit_bytes_total{name=~"%s.*"}[10s])) by (name)' % self.sliceID
                PARAMS = {'query': query, 'time': timestamp}

                request = requests.get(url = URL, params = PARAMS)
                metricV2 = json.loads(request.text)
                print("Métrica 2: %s\n" % metricV2)

                #Métrica 3: Virtual CPU
                query = 'sum(rate(container_cpu_usage_seconds_total{name=~"%s.*"}[10s])) by (name) * 100' % self.sliceID
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
                query = 'sum(rate(container_network_receive_bytes_total{id="/"}[10s])) by (id)'
                PARAMS = {'query': query, 'time': timestamp}

                request = requests.get(url = URL, params = PARAMS)
                metricP1 = json.loads(request.text)
                print("Métrica P1: %s" % metricP1)

                #Métrica 2: Physical Network transmit
                query = 'sum(rate(container_network_transmit_bytes_total{id="/"}[10s])) by (id)'
                PARAMS = {'query': query, 'time': timestamp}

                request = requests.get(url=URL, params=PARAMS)
                metricP2 = json.loads(request.text)
                print("Métrica P2: %s" % metricP2)

                #Métrica 3: Physical CPU
                query = 'sum(sum by (container_name)( rate(container_cpu_usage_seconds_total[10s] ) )) / count(node_cpu_seconds_total{mode="system"}) * 100'
                PARAMS = {'query': query, 'time': timestamp}

                request = requests.get(url=URL, params=PARAMS)
                metricP3 = json.loads(request.text)
                print("Métrica P3: %s" % metricP3)

                #Métrica 4: Physical RAM
                query = 'sum(node_memory_MemTotal_bytes) - sum(node_memory_MemAvailable_bytes)'
                PARAMS = {'query': query, 'time': timestamp}

                request = requests.get(url=URL, params=PARAMS)
                metricP4 = json.loads(request.text)
                print("Métrica P4: %s" % metricP4)

                physicalMetrics = [metricP1, metricP2, metricP3, metricP4]
                virtualMetricsDB(virtualMetrics, self.cnx, i, self.sliceID)



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

                time.sleep(10)





agentsList = ['slice1', ['200.136.191.94'], 'slice2', ['200.136.191.111']]
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

threadSlice1 = sliceThread(agentsList[0], agentsList[1], cnx)
threadSlice2 = sliceThread(agentsList[2], agentsList[3], cnx2)

threadSlice1.start()
threadSlice2.start()







