
import datetime
import json
from time import sleep
from typing import Any, Callable, Dict, List, Optional, Type
from utils import Blind, BlindCommand, BlindState, MQTTConfig, load_config
import paho.mqtt.client as paho_mqtt

MoveBlindCallback = Callable[[Blind, BlindCommand, Optional[Type['MQTT']]], None]

class MQTT:
    def __init__(self, config: MQTTConfig, blinds: List[Blind], move_blind_callback: Optional[MoveBlindCallback] = None, debug: bool = False):
        self.config = config
        self.blinds = blinds
        self.move_blind_callback = move_blind_callback
        self.debug = debug
        self.mqtt_client = paho_mqtt.Client(callback_api_version=paho_mqtt.CallbackAPIVersion.VERSION2)
        self.init_callbacks()
        self.connect(config.host, config.port, config.username, config.password)

    def log(self, debug: bool = False, **kwargs: Any):
        if not debug or self.debug:
            print(datetime.datetime.now(), ' '.join(f'{key}={value}' for key, value in kwargs.items()))

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

        topic_parts = message.topic.split('/')
        if len(topic_parts) != 5 or topic_parts[0] != self.config.topic or topic_parts[1] != 'blinds' or topic_parts[2] != 'mediola1' or topic_parts[4] != 'set': # FIXME mediola1 -> mediola
            self.log(debug=False, error=f'got invalid topic: {message.topic}')
            return
        blind_id_parts = topic_parts[3].split('_')
        if len(blind_id_parts) != 2 or blind_id_parts[0] != 'ER':
            self.log(debug=False, error=f'got invalid blind id: {message.topic}')
            return
        
        blind_adr = blind_id_parts[1]
        blind = next((b for b in self.blinds if b.adr == blind_adr), [None])
        if blind is None:
            self.log(debug=False, error=f'cannot find blind with adress {blind_adr}')
            return
        
        command = None
        if message.payload == b'open':
            command = BlindCommand.OPEN
        elif message.payload == b'close':
            command = BlindCommand.CLOSE
        elif message.payload == b'stop':
            command = BlindCommand.STOP
        if command is None:
            self.log(debug=False, error=f'cannot interpret payload (command) {message.payload.decode("utf-8")}')
            return        

        if self.move_blind_callback is not None:
            self.move_blind_callback(blind, command, self)


    def setup_discovery(self):
        for blind in self.blinds:
            identifier = f'ER_{blind.adr}'
            deviceid = f'mediola_blinds_{self.config.host.replace(".", "")}'
            dtopic = f'{self.config.discovery_prefix}/cover/mediola_{identifier}/config'
            topic = f'{self.config.topic}/blinds/mediola1/{identifier}' # FIXME mediola1 -> mediola

            payload = {
                'command_topic': f'{topic}/set',
                'payload_open': 'open',
                'payload_close': 'close',
                'payload_stop': 'stop',
                'optimistic': False,
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
        topic = f'{self.config.topic}/blinds/mediola1/{identifier}/state' # FIXME mediola1 -> mediola
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
    m.publish_blind_state(config.blinds[2], BlindState.CLOSED)
    sleep(5)