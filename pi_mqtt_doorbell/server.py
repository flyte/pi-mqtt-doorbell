import argparse
import logging
import yaml
from time import sleep

import RPi.GPIO as gpio
import paho.mqtt.client as mqtt


RECONNECT_DELAY_SECS = 5

_LOG = logging.getLogger(__name__)
_LOG.addHandler(logging.StreamHandler())
_LOG.setLevel(logging.DEBUG)


def on_disconnect(client, userdata, rc):
    _LOG.warning("Disconnected from MQTT server with code: %s" % rc)
    while rc != 0:
        sleep(RECONNECT_DELAY_SECS)
        rc = client.reconnect()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("config")
    args = p.parse_args()

    with open(args.config) as f:
        config = yaml.load(f)

    client = mqtt.Client()
    user = config["mqtt"].get("user")
    password = config["mqtt"].get("password")

    if user and password:
        client.username_pw_set(user, password)

    def on_conn(client, userdata, flags, rc):
        client.subscribe(config["mqtt"]["bell_topic"], qos=1)
        _LOG.info("Subscribed to topic: %r", config["mqtt"]["bell_topic"])

    def on_msg(client, userdata, msg):
        _LOG.info("Got message on topic %r: %r", msg.topic, msg.payload)
        if msg.payload == config["mqtt"]["ding_payload"]:
            _LOG.info("Ding dong!")
            for _ in range(config["bell"]["ding_dong_count"]):
                gpio.output(config["bell"]["pin"], config["bell"]["ding_value"])
                sleep(config["bell"]["dong_delay"])
                gpio.output(
                    config["bell"]["pin"], not config["bell"]["ding_value"])
                sleep(config["bell"]["repeat_delay"])

    client.on_disconnect = on_disconnect
    client.on_connect = on_conn
    client.on_message = on_msg

    gpio.setmode(gpio.BCM)
    gpio.setup(config["bell"]["pin"], gpio.OUT)

    client.connect(config["mqtt"]["host"], config["mqtt"]["port"], 60)
    client.loop_start()

    try:
        while True:
            sleep(60)
    except KeyboardInterrupt:
        print ""
    finally:
        client.loop_stop()
