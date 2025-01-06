
import datetime
from threading import Timer, Thread
import time
import json
import requests
from typing import Optional

from mqtt import MQTT
from utils import Blind, BlindCommand, BlindState


class Mediola:
    host: str
    password: str
    
    def __init__(self, host: str, password: str, follow_up_time: int):
        self.host = host
        self.password = password
        self.follow_up_time = follow_up_time
        self.commandstrings = {
            BlindCommand.OPEN: "01",
            BlindCommand.CLOSE: "00",
            BlindCommand.STOP: "02"
        }
    
    def _request(self, payload: dict) -> dict:
        url = 'http://' + self.host + '/command'
        if len(self.password) > 0:
            payload['XC_USER'] = 'user'
            payload['XC_PASS'] = self.password
        response = requests.get(url, params=payload, headers={'Connection':'close'})
        #assert response.text[:8] == '{XC_SUC}'
        if len(response.text) > 8:
            return json.loads(response.text[8:])
        else:
            print(f'{datetime.datetime.now()} no response payload. Got response "{response.text}" for request payload {payload}')
            return {}
    
    def _request_blind_state(self, blind: Blind) -> BlindState:
        # sometimes XC_ERR is thrown, just try again after a second
        while True:
            response = self._request({'XC_FNC': 'refresher', 'adr': format(int(blind.adr), "02x")})
            if 'state' in response:
                break
            time.sleep(1)

        print(f'{datetime.datetime.now()} Response for state request of blind {blind} is {response}')
        if response['state'] == 'A201':
            return BlindState.OPENED
        elif response['state'] == 'A202':
            return BlindState.CLOSED
        elif response['state'] == 'A20A':
            return BlindState.OPENING
        elif response['state'] == 'A20B':
            return BlindState.CLOSING
        elif response['state'] == 'A20D':
            return BlindState.STOPPED
        else:
            return BlindState.UNKNOWN
    
    def _command_blind(self, blind: Blind, command: BlindCommand):
        self._request({
            'XC_FNC': 'SendSC',
            'type': 'ER',
            'data': format(int(blind.adr), "02x") + self.commandstrings[command]
        })

    def get_blind_state(self, blind: Blind, follow_up_if_moving: bool, mqtt: Optional[MQTT]):
        state = self._request_blind_state(blind)
        if mqtt is not None:
            mqtt.publish_blind_state(blind, state)
        if follow_up_if_moving and state in (BlindState.OPENING, BlindState.CLOSING):
            print(f'{datetime.datetime.now()} Blind {blind} is moving ({state}). Starting another timer to follow up')
            Timer(self.follow_up_time, self.get_blind_state, (blind, True, mqtt)).start()
        return state

    def _move_blind(self, blind: Blind, command: BlindCommand, mqtt: Optional[MQTT]):
        success_states = []
        if command == BlindCommand.OPEN:
            success_states.append(BlindState.OPENING)
            success_states.append(BlindState.OPENED)
        elif command == BlindCommand.CLOSE:
            success_states.append(BlindState.CLOSING)
            success_states.append(BlindState.CLOSED)
        else: #command == BlindCommand.STOP:
            success_states.append(BlindState.STOPPED)

        while True:
            print(f'{datetime.datetime.now()} sending command {command} for blind {blind}')
            self._command_blind(blind, command)
            time.sleep(1)
            if self.get_blind_state(blind, follow_up_if_moving=True, mqtt=mqtt) in success_states:
                break

    def move_blind(self, blind: Blind, command: BlindCommand, mqtt: Optional[MQTT]):
        # perform moving blind in thread to enable immediate return.
        # Otherwise if multiple blinds are moved in a row, they need to wait until
        # preceeding blinds have confirmed that they are moving
        Thread(target=self._move_blind, args=(blind, command, mqtt)).start()

