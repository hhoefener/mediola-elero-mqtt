
from mediola import Mediola
from mqtt import MQTT, MQTTdummy
from utils import BlindCommand, load_config


def main():
    config = load_config()
    mediola = Mediola(config.mediola.host, config.mediola.password, config.mediola.follow_up_time)
    mqtt = MQTTdummy()

    for blind in config.blinds:
        mediola.move_blind(blind, BlindCommand.OPEN, mqtt)


if __name__ == '__main__':
    main()