
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

import yaml

class BlindState(Enum):
    OPENED = (0, "opened")
    CLOSED = (1, "closed")
    OPENING = (2, "opening")
    CLOSING = (3, "closing")
    STOPPED = (4, "stopped")
    UNKNOWN = (5, "unknown")

    def __init__(self, state_code, state_text):
        self.state_code = state_code
        self.state_text = state_text

    @property
    def text(self):
        return self.state_text

class BlindCommand(Enum):
    OPEN = 1
    CLOSE = 2
    STOP = 3

@dataclass
class Blind:
    adr: str
    name: str

    def __init__(self, data: Dict):
        self.adr = data['adr']
        self.name = data['name']

@dataclass
class MediolaConfig:
    host: str
    password: str
    follow_up_time: int

    def __init__(self, data):
        self.host = data['host']
        self.password = data['password'] if data['password'] is not None else ""
        self.follow_up_time = data['follow_up_time']

@dataclass
class MQTTConfig:
    host: str
    port: int
    username: str
    password: str
    discovery_prefix: str
    topic: str
    debug: bool

    def __init__(self, data):
        self.host = data['host']
        self.port = data['port']
        self.username = data['username']
        self.password = data['password']
        self.discovery_prefix = data['discovery_prefix']
        self.topic = data['topic']
        self.debug = data['debug']

@dataclass
class Config:
    mediola: MediolaConfig
    mqtt: MQTTConfig
    blinds: List[Blind]

    def __init__(self, data: Dict):
        self.mediola = MediolaConfig(data['mediola'][0])
        self.mqtt = MQTTConfig(data['mqtt'])
        self.blinds = [Blind(blind_data) for blind_data in data['blinds']]

def load_config() -> Config:
    with open('mediola2mqtt.yaml', 'r') as fp:
        data = yaml.safe_load(fp)
        config = Config(data)
    return config