
import datetime
import json
from typing import Any, Dict, List
from utils import Blind, BlindState, MQTTConfig, load_config
import paho.mqtt.client as paho_mqtt

class MQTT:
    def __init__(self, config: MQTTConfig, blinds: List[Blind]):
        self.config = config
        self.blinds = blinds
        self.mqtt_client = paho_mqtt.Client()
        self.init_callbacks()
        self.connect()

    def init_callbacks(self):
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_disconnect = self.on_disconnect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_log = lambda client, obj, level, string: print(f'{datetime.datetime.now()} - level {level}: {string}')
        self.mqtt_client.on_publish = lambda client, obj, mid: print(f'{datetime.datetime.now()} - on_publish: {mid}')
        self.mqtt_client.on_subscribe = lambda client, obj, mid, granted_qos: print(f'{datetime.datetime.now()} - subscribed {mid} granted_qos {granted_qos}')

    def connect(self, host: str, port: int, username: str, password: str):
        self.mqtt_client.username_pw_set(username=username, password=password)
        self.mqtt_client.connect(host=host, port=port, keepalive=60)

    def on_connect(self, client: paho_mqtt.Client, userdata: Any, flags: Dict, reason_code: paho_mqtt.ReasonCode):
        if reason_code.is_failure:
            raise ValueError(f'Error on connecting to MQTT broker: {reason_code.getName()}')
        self.setup_discovery()

    def on_disconnect(self, client: paho_mqtt.Client, userdata: Any, reason_code: paho_mqtt.ReasonCode):
        if reason_code.is_failure:
            raise ValueError(f'Unexpected disconnect from MQTT broker: {reason_code.getName()}')
        print("Disconnected")

    def on_message(self, client: paho_mqtt.Client, userdata: Any, message: paho_mqtt.MQTTMessage):
        print("Msg: " + message.topic + " " + str(message.qos) + " " + str(message.payload))
        # # Here we should send a HTTP request to Mediola to open the blind
        # dtype, adr = message.topic.split("_")
        # mediolaid = dtype.split("/")[-2]
        # dtype = dtype[dtype.rfind("/")+1:]
        # adr = adr[:adr.find("/")]
        # for ii in range(0, len(config['blinds'])):
        #     if dtype == config['blinds'][ii]['type'] and adr == config['blinds'][ii]['adr']:
        #         if isinstance(config['mediola'], list):
        #             if config['blinds'][ii]['mediola'] != mediolaid:
        #                 continue
        #         if message.payload == b'open':
        #             if dtype == 'RT':
        #                 data = "20" + adr
        #             elif dtype == 'ER':
        #                 data = format(int(adr), "02x") + "01"
        #             else:
        #                 return
        #         elif message.payload == b'close':
        #             if dtype == 'RT':
        #                 data = "40" + adr
        #             elif dtype == 'ER':
        #                 data = format(int(adr), "02x") + "00"
        #             else:
        #                 return
        #         elif message.payload == b'stop':
        #             if dtype == 'RT':
        #                 data = "10" + adr
        #             elif dtype == 'ER':
        #                 data = format(int(adr), "02x") + "02"
        #             else:
        #                 return
        #         else:
        #             print("Wrong command")
        #             return
        #         payload = {
        #         "XC_FNC" : "SendSC",
        #         "type" : dtype,
        #         "data" : data
        #         }
        #         host = ''
        #         if isinstance(config['mediola'], list):
        #             mediolaid = config['blinds'][ii]['mediola']
        #             for jj in range(0, len(config['mediola'])):
        #                 if mediolaid == config['mediola'][jj]['id']:
        #                     host = config['mediola'][jj]['host']
        #                 if 'password' in config['mediola'][jj] and config['mediola'][jj]['password'] != '':
        #                     payload['XC_PASS'] = config['mediola'][jj]['password']
        #         else:
        #             host = config['mediola']['host']
        #             if 'password' in config['mediola'] and config['mediola']['password'] != '':
        #                 payload['XC_PASS'] = config['mediola']['password']
        #         if host == '':
        #             print('Error: Could not find matching Mediola!')
        #             return
        #         url = 'http://' + host + '/command'
        #         response = requests.get(url, params=payload, headers={'Connection':'close'})

    def setup_discovery(self):
        for blind in self.blinds:
            identifier = f'{blind.type}_{blind.adr}'
            deviceid = f'mediola_blinds_{self.config.host.replace(".", "")}'
            dtopic = f'{self.config.discovery_prefix}/cover/mediola_{identifier}/config'
            topic = f'{self.config.topic}/blinds/mediola/{identifier}'

            payload = {
                'command_topic': f'{topic}/set',
                'payload_open': 'open',
                'payload_close': 'close',
                'payload_stop': 'stop',
                'optimistic': True,
                'device_class': 'blind',
                'unique_id': f'mediola_{identifier}',
                'name': blind.name,
                'device' : {
                    'identifiers': deviceid,
                    'manufacturer': 'Mediola',
                    'name': 'Mediola Blind',
                },
                'state_topic': f'{topic}/state'
            }

            self.mqtt_client.subscribe(f'{topic}/set')
            self.mqtt_client.publish(dtopic, payload=json.dumps(payload), retain=True)
        
    def publish_blind_state(self, blind: Blind, state: BlindState):
        print(f'{datetime.datetime.now()} publishing blind {blind} state {state}')


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

class MQTTdummy(MQTT):
    def __init__(self):
        pass

    def publish_blind_state(self, blind: Blind, state: BlindState):
        print(f'{datetime.datetime.now()} publishing blind {blind} state {state}')


#config = load_config()
#mqtt = MQTT(config.mqtt, config.blinds)