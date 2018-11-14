import requests
import json
import threading
import time

class sliceThread (threading.Thread):
    def __init__(self, sliceID, agents):
        threading.Thread.__init__(self)
        self.sliceID = sliceID
        self.agents = agents
        print(sliceID, agents)

    def run(self):
        while (True):
            print("Starting Collecting Metrics from {} Agents: {}\n".format(self.sliceID,self.agents))


            for i in self.agents:
                URL = "http://%s:9090/api/v1/query?" % i
                #print(URL)

                # Métrica 1: Virtual network receive
                query = 'sum(rate(container_network_receive_bytes_total{name=~"%s.*"}[10s])) by (name)' % self.sliceID
                #print(query)
                PARAMS = {'query': query}

                request = requests.get(url = URL, params = PARAMS)
                metricV1 = json.loads(request.text)
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





agentsList = ['slice1', ['200.136.191.111'], 'slice2', ['200.136.191.94']]
#for key, value in agentsList.items():

threadSlice1 = sliceThread(agentsList[0], agentsList[1])
threadSlice2 = sliceThread(agentsList[2], agentsList[3])

threadSlice1.start()
threadSlice2.start()





