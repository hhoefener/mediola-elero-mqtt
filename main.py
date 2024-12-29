
from mediola import Mediola
from mqtt import MQTT
from utils import BlindCommand, load_config


def main():
    config = load_config()
    mediola = Mediola(config.mediola.host, config.mediola.password, config.mediola.follow_up_time)
    mqtt = MQTT()

    mediola.move_blind(config.blinds[0], BlindCommand.OPEN, mqtt)


if __name__ == '__main__':
    main()