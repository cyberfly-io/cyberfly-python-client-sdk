from pypact.pact import Pact
from cyberflySdk import config, utils
import time


def get_rules(device_id: str, network_id: str, key_pair: dict) -> list:
    pact = Pact()
    pact_code = '({}.read-device-rules "{}")'.format(config.contract, device_id)
    cmd = {
        "pactCode": pact_code,
        "envData": {},
        "meta": utils.default_meta(),
        "networkId": network_id,
        "nonce": time.time().__round__() - 15,
        "keyPairs": [key_pair]
    }
    try:
        rules = pact.fetch.local(cmd, utils.get_api_host(network_id))
        if isinstance(rules, dict) and rules.get('result')['status'] == "success":
            return rules.get('result')['data']
        else:
            return []
    except Exception as e:
        print(e.__str__())
        return []


def get_device(device_id: str, network_id: str, key_pair: dict) -> dict:
    conn = False
    while not conn:
        if utils.is_cnx_active() is True:
            conn = True
            pact = Pact()
            pact_code = '({}.get-device "{}")'.format(config.contract, device_id)
            cmd = {
                "pactCode": pact_code,
                "envData": {},
                "meta": utils.default_meta(),
                "networkId": network_id,
                "nonce": time.time().__round__() - 15,
                "keyPairs": [key_pair]
            }
            try:
                devices = pact.fetch.local(cmd, utils.get_api_host(network_id))
                if isinstance(devices, dict) and devices.get('result')['status'] == "success":
                    return devices.get('result')['data']
                else:
                    return {}
            except Exception as e:
                print(e.__str__())
                return {}
        else:
            print("no internet")

