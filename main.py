
from mediola import Mediola
from mqtt import MQTT, MQTTdummy
from utils import BlindCommand, load_config


def main():
    config = load_config()
    mediola = Mediola(config.mediola.host, config.mediola.password, config.mediola.follow_up_time, debug=True)
    mqtt = MQTT(config.mqtt, config.blinds, move_blind_callback=mediola.move_blind, debug=True)
    
    mqtt.loop_forever()

if __name__ == '__main__':
    main()