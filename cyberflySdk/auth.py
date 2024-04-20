import json

from pypact.pact import Pact
import time

pact = Pact()


def check_auth(cmd, device_info):
    pub_key = cmd.get('pubKey')
    sig = cmd.get('sig')
    device_exec = cmd.get('device_exec')
    if pub_key and sig and device_exec:
        verify = pact.crypto.verify(device_exec, pub_key, sig)
        if verify:
            device = device_info
            if device.keys() and pub_key in device['guard']['keys']:
                print("auth passed")
                return True
            else:
                print("failed")
                return False
        else:
            return False
    else:
        print("Mission anyone of these variable pubKey, sig, device_exec")
        return False


def validate_expiry(msg):
    expiry_time = msg.get('expiry_time')
    if expiry_time:
        now = time.time().__round__()
        if now < expiry_time:
            print("validity passed")
            return True
        else:
            print("Time expired")
            return False
    else:
        print("expiry_time required")
        return False