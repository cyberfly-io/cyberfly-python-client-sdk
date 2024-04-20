import socketio
from cyberflySdk.config import node_url
from cyberflySdk import utils, api, auth
import rule_engine
import json


class CyberflyClient:
    def __init__(self, device_id: str, key_pair: dict,
                 network_id: str = "mainnet01", node_url=node_url):
        self.sio = socketio.Client()
        self.key_pair = key_pair
        self.network_id = network_id
        self.device_data = {}
        self.device_id = device_id
        self.topic = device_id
        self.account = "k:" + self.key_pair.get("publicKey")
        self.caller = default_callback
        self.node_url = node_url
        self.rules = []
        self.device_info = {}
        self.update_device()
        self.update_rules()
        self.connect()
        self.sio.on("onmessage", self.on_received)

    def on_received(self, data):
        try:
            msg = json.loads(data['message'])
            json_data = json.loads(msg)
            device_exec = json.loads(json_data.get('device_exec'))
            response_topic = device_exec.get('response_topic')
            if auth.validate_expiry(device_exec) \
                    and auth.check_auth(json_data, self.device_info):
                try:
                    if device_exec.get('update_rules'):
                        self.update_rules()
                    if device_exec.get('update_device'):
                        self.update_device()
                    self.caller(device_exec)
                    if response_topic:
                        signed = utils.make_cmd({"info": "success"}, self.key_pair)
                        utils.sio_publish(self.sio, response_topic, signed)
                except Exception as e:
                    signed = utils.make_cmd({"info": "error"}, self.key_pair)
                    utils.sio_publish(self.sio, response_topic, signed)
                    print(e.__str__())
            else:
                print(self.device_info)
                print("auth failed")
        except Exception as e:
            print(e.__str__())

    def connect(self):
        try:
            self.sio.connect(self.node_url)
            self.subscribe(self.topic)
        except Exception as e:
            print(e.__str__())
            self.connect()

    def subscribe(self, topic):
        try:
            self.sio.emit('subscribe', topic)
        except Exception as e:
            print(e.__str__())
            self.connect()

    def publish(self, topic, msg):
        signed = utils.make_cmd(msg, self.key_pair)
        utils.sio_publish(self.sio, topic, signed)

    def update_data(self, key: str, value):
        self.device_data.update({key: value})

    def on_message(self):
        def decorator(callback_function):
            self.caller = callback_function
        return decorator

    def process_rules(self, data: dict):
        rules = self.rules
        if len(rules) == 0:
            self.update_rules()
        context = rule_engine.Context(default_value=None)
        for rule in rules:
            rul = rule_engine.Rule(utils.make_rule(rule['rule']), context=context)
            try:
                if rul.matches(data):
                    utils.publish(self.sio, rule['action'], self.key_pair)
            except Exception as e:
                print(e.__str__())

    def process_schedule(self, data: dict):
        pass

    def update_rules(self):
        rules = api.get_rules(self.device_id, self.network_id, self.key_pair)
        self.rules = rules

    def update_device(self):
        device = api.get_device(self.device_id, self.network_id, self.key_pair)
        self.device_info = device

    def store_data(self, data):
        signed = utils.make_cmd_to_store(data, self.key_pair)
        #need to implement


def default_callback(data):
    pass