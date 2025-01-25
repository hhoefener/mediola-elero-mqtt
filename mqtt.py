
import datetime
import json
from time import sleep
from typing import Any, Dict, List, Optional
from utils import Blind, BlindState, MQTTConfig, load_config
import paho.mqtt.client as paho_mqtt

class MQTT:
    def __init__(self, config: MQTTConfig, blinds: List[Blind], debug: bool = False):
        self.config = config
        self.blinds = blinds
        self.debug = debug
        self.mqtt_client = paho_mqtt.Client(callback_api_version=paho_mqtt.CallbackAPIVersion.VERSION2)
        self.init_callbacks()
        self.connect(config.host, config.port, config.username, config.password)

    def log(self, debug: bool = False, **kwargs: Any):
        if not debug or self.debug:
            print(datetime.datetime.now(), ' '.join(f'{key}={value}' for key, value in kwargs.items()))

#    def log(self, debug: bool = False, *args: Any, **kwargs: Any):
#        if not debug or self.debug:
#            values = ' '.join(map(str, args))
#            if kwargs:
#                kwarg_values = ' '.join(f'{key}={value}' for key, value in kwargs.items())
#                values = f'{values} {kwarg_values}'
#            print(datetime.datetime.now(), values)

    def loop_start(self):
        self.mqtt_client.loop_start()

    def loop_forever(self):
        self.mqtt_client.loop_forever()

    def init_callbacks(self):
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_disconnect = self.on_disconnect
        self.mqtt_client.on_message = self.on_message

        self.mqtt_client.on_log = lambda *args, **kwargs: self.log(debug=True, method='on_log', args=args **kwargs)
        self.mqtt_client.on_publish = lambda *args, **kwargs: self.log(debug=True, method='on_publish', args=args, **kwargs)
        self.mqtt_client.on_subscribe = lambda *args, **kwargs: self.log(debug=True, method='on_subscribe', args=args, **kwargs)

    def connect(self, host: str, port: int, username: str, password: str):
        self.mqtt_client.username_pw_set(username=username, password=password)
        self.mqtt_client.connect(host=host, port=port, keepalive=60)

    def on_connect(self, client: paho_mqtt.Client, userdata: Any, flags: Dict, reason_code: paho_mqtt.ReasonCode, properties: paho_mqtt.Properties):
        if reason_code.is_failure:
            raise ValueError(f'Error on connecting to MQTT broker: {reason_code.getName()}')
        self.setup_discovery()

    def on_disconnect(self, client: paho_mqtt.Client, userdata: Any, reason_code: paho_mqtt.ReasonCode):
        if reason_code.is_failure:
            raise ValueError(f'Unexpected disconnect from MQTT broker: {reason_code.getName()}')
        print("Disconnected")

    def on_message(self, client: paho_mqtt.Client, userdata: Any, message: paho_mqtt.MQTTMessage):
        # FIXME
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
            identifier = f'ER_{blind.adr}'
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
        identifier = f'ER_{blind.adr}'
        topic = f'{self.config.topic}/blinds/mediola/{identifier}/state'
        self.mqtt_client.publish(topic, payload=state.text, retain=True)
        self.log(debug=True, args=f'Published state {state} for blind {blind} to topic {topic}')


class MQTTdummy(MQTT):
    def __init__(self):
        pass

    def publish_blind_state(self, blind: Blind, state: BlindState):
        print(f'{datetime.datetime.now()} publishing blind {blind} state {state}')


if __name__ == '__main__':
    config = load_config()
    m = MQTT(config.mqtt, config.blinds, debug=True)
    m.loop_start()
    sleep(5)
    m.publish_blind_state(config.blinds[0], BlindState.OPENED)
    sleep(5)