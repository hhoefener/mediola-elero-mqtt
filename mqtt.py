
import datetime
from utils import Blind, BlindState
import paho.mqtt.client as paho_mqtt


class MQTT:
    def __init__(self):
        self.mqtt_client = paho_mqtt.Client()

    def init_callbacks(self):
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_disconnect = self.on_disconnect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_log = lambda client, obj, level, string: print(f'{datetime.datetime.now()} - level {level}: {string}')
        self.mqtt_client.on_publish = lambda client, obj, mid: print(f'{datetime.datetime.now()} - on_publish: {mid}')
        self.mqtt_client.on_subscribe = lambda client, obj, mid, granted_qos: print(f'{datetime.datetime.now()} - subscribed {mid} granted_qos {granted_qos}')
        self.connect()

    def connect(self, host: str, port: int, username: str, password: str):
        self.mqtt_client.username_pw_set(username=username, password=password)
        self.mqtt_client.connect(host=host, port=port, keepalive=60)

    def on_mqtt_connect(client, userdata, flags, rc):
        connect_statuses = {
            0: "Connected",
            1: "incorrect protocol version",
            2: "invalid client ID",
            3: "server unavailable",
            4: "bad username or password",
            5: "not authorised"
        }
        if rc != 0:
            print("MQTT: " + connect_statuses.get(rc, "Unknown error"))
        else:
            MQTT.setup_discovery(config, client)

    def on_mqtt_disconnect(client, userdata, rc):
        if rc != 0:
            print("Unexpected disconnection")
        else:
            print("Disconnected")

    def on_mqtt_message(client, obj, msg):
        print("Msg: " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
        # Here we should send a HTTP request to Mediola to open the blind
        dtype, adr = msg.topic.split("_")
        mediolaid = dtype.split("/")[-2]
        dtype = dtype[dtype.rfind("/")+1:]
        adr = adr[:adr.find("/")]
        for ii in range(0, len(config['blinds'])):
            if dtype == config['blinds'][ii]['type'] and adr == config['blinds'][ii]['adr']:
                if isinstance(config['mediola'], list):
                    if config['blinds'][ii]['mediola'] != mediolaid:
                        continue
                if msg.payload == b'open':
                    if dtype == 'RT':
                        data = "20" + adr
                    elif dtype == 'ER':
                        data = format(int(adr), "02x") + "01"
                    else:
                        return
                elif msg.payload == b'close':
                    if dtype == 'RT':
                        data = "40" + adr
                    elif dtype == 'ER':
                        data = format(int(adr), "02x") + "00"
                    else:
                        return
                elif msg.payload == b'stop':
                    if dtype == 'RT':
                        data = "10" + adr
                    elif dtype == 'ER':
                        data = format(int(adr), "02x") + "02"
                    else:
                        return
                else:
                    print("Wrong command")
                    return
                payload = {
                "XC_FNC" : "SendSC",
                "type" : dtype,
                "data" : data
                }
                host = ''
                if isinstance(config['mediola'], list):
                    mediolaid = config['blinds'][ii]['mediola']
                    for jj in range(0, len(config['mediola'])):
                        if mediolaid == config['mediola'][jj]['id']:
                            host = config['mediola'][jj]['host']
                        if 'password' in config['mediola'][jj] and config['mediola'][jj]['password'] != '':
                            payload['XC_PASS'] = config['mediola'][jj]['password']
                else:
                    host = config['mediola']['host']
                    if 'password' in config['mediola'] and config['mediola']['password'] != '':
                        payload['XC_PASS'] = config['mediola']['password']
                if host == '':
                    print('Error: Could not find matching Mediola!')
                    return
                url = 'http://' + host + '/command'
                response = requests.get(url, params=payload, headers={'Connection':'close'})

        
    def publish_blind_state(self, blind: Blind, state: BlindState):
        print(f'publishing blind {blind} state {state}')





# class MQTT:
#     mqtt_client: mqtt.Client

#     def __init__(self, username: str, password: str, host: str, port: int):
#         self.mqtt_client = mqtt.Client()
#         self.mqtt_client.on_connect = MQTT.on_mqtt_connect
#         self.mqtt_client.on_disconnect = MQTT.on_mqtt_disconnect
#         self.mqtt_client.on_message = MQTT.on_mqtt_message
#         self.mqtt_client.on_log = lambda client, obj, level, string: print(f'{datetime.datetime.now()} - level {level}: {string}')
#         self.mqtt_client.on_publish = lambda client, obj, mid: print(f'{datetime.datetime.now()} - on_publish: {mid}')
#         self.mqtt_client.on_subscribe = lambda client, obj, mid, granted_qos: print(f'{datetime.datetime.now()} - subscribed {mid} granted_qos {granted_qos}')
#         

#     # Define MQTT event callbacks
#     
#     def setup_discovery(config: dict, mqtt_client: mqtt.Client):
#         if 'blinds' in config:
#             for ii in range(0, len(config['blinds'])):
#                 identifier = config['blinds'][ii]['type'] + '_' + config['blinds'][ii]['adr']
#                 host = ''
#                 mediolaid = 'mediola'
#                 if isinstance(config['mediola'], list):
#                     mediolaid = config['blinds'][ii]['mediola']
#                     for jj in range(0, len(config['mediola'])):
#                         if mediolaid == config['mediola'][jj]['id']:
#                             host = config['mediola'][jj]['host']
#                 else:
#                     host = config['mediola']['host']
#                 if host == '':
#                     print('Error: Could not find matching Mediola!')
#                     continue
#                 deviceid = "mediola_blinds_" + host.replace(".", "")
#                 dtopic = config['mqtt']['discovery_prefix'] + '/cover/' + \
#                         mediolaid + '_' + identifier + '/config'
#                 topic = config['mqtt']['topic'] + '/blinds/' + mediolaid + '/' + identifier
#                 name = "Mediola Blind"
#                 if 'name' in config['blinds'][ii]:
#                     name = config['blinds'][ii]['name']

#                 payload = {
#                 "command_topic" : topic + "/set",
#                 "payload_open" : "open",
#                 "payload_close" : "close",
#                 "payload_stop" : "stop",
#                 "optimistic" : True,
#                 "device_class" : "blind",
#                 "unique_id" : mediolaid + '_' + identifier,
#                 "name" : name,
#                 "device" : {
#                     "identifiers" : deviceid,
#                     "manufacturer" : "Mediola",
#                     "name" : "Mediola Blind",
#                 },
#                 }
#                 if config['blinds'][ii]['type'] == 'ER':
#                     payload["state_topic"] = topic + "/state"
#                 payload = json.dumps(payload)
#                 mqtt_client.subscribe(topic + "/set")
#                 mqtt_client.publish(dtopic, payload=payload, retain=True)

# def handle_blind(packet_type, address, state, mediolaid):
#     retain = True
#     topic = False
#     payload = False

#     for ii in range(0, len(config['blinds'])):
#         if packet_type == 'ER' and packet_type == config['blinds'][ii]['type']:
#             if address == config['blinds'][ii]['adr'].lower():
#                 if isinstance(config['mediola'], list):
#                     if config['blinds'][ii]['mediola'] != mediolaid:
#                         continue
#                 identifier = config['blinds'][ii]['type'] + '_' + config['blinds'][ii]['adr']
#                 topic = config['mqtt']['topic'] + '/blinds/' + mediolaid + '/' + identifier + '/state'
#                 payload = 'unknown'
#                 if state == '01' or state == '0e':
#                     payload = 'open'
#                 elif state == '02' or state == '0f':
#                     payload = 'closed'
#                 elif state == '08' or state == '0a':
#                     payload = 'opening'
#                 elif state == '09' or state == '0b':
#                     payload = 'closing'
#                 elif state == '0d' or state == '05':
#                     payload = 'stopped'
#     return topic, payload, retain

# def start_mqtt_client(config):
#     # Setup MQTT connection
#     mqttc = mqtt.Client()

#     mqttc.on_connect = on_mqtt_connect
#     mqttc.on_subscribe = on_mqtt_subscribe
#     mqttc.on_disconnect = on_mqtt_disconnect
#     mqttc.on_message = on_mqtt_message

#     if config['mqtt']['username'] and config['mqtt']['password']:
#         mqttc.username_pw_set(config['mqtt']['username'], config['mqtt']['password'])
#     try:
#         mqttc.connect(config['mqtt']['host'], config['mqtt']['port'], 60)
#     except:
#         print('Error connecting to MQTT, will now quit.')
#         sys.exit(1)
#     mqttc.loop_start()
