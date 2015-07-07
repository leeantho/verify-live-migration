"""
verify_live_migration_client.py

Description:
    A sample client that interacts with and tests the verify_live_migration
    flask server.

Usage:
    # Start the flask server API.
    python verify_live_migration.py -port 5005
    # Run the client, specifying optional arguments as needed.
    python verify_live_migration_client.py -port 5005
"""
from os_brick.initiator import connector
from cinderclient.v2 import client

import argparse
import pprint
import requests
import os
import json

parser = argparse.ArgumentParser()
parser.add_argument("-username", help="username", default=os.environ['OS_USERNAME'])
parser.add_argument("-password", help="password", default=os.environ['OS_PASSWORD'])
parser.add_argument("-tenant", help="tenant name", default=os.environ['OS_TENANT_NAME'])
parser.add_argument("-auth", help="auth url", default=os.environ['OS_AUTH_URL'])
parser.add_argument("-root-helper", help="root helper", default="sudo")
parser.add_argument("-ip", help="ip of flask server", default="localhost")
parser.add_argument("-port", help="port of flask server", default=5002, type=int)
args = parser.parse_args()

ROOT_HELPER = args.root_helper
USER = args.username
PASS = args.password
TENANT = args.tenant
AUTH_URL = args.auth
FLASK_URL = "http://%s:%s/" % (args.ip, args.port)

FC_VOL = "a76487bc-7efc-4879-a34f-9e3f47316da2"
ISCSI_VOL = "e66a51ec-979f-43c1-8e9d-ebd74b9de9e4"

def fc_test():
    print("---- Testing FC ----")
    cinder = client.Client(USER, PASS, TENANT, AUTH_URL, service_type="volume")

    # Use os_brick to get needed connection properties.
    connector_props = connector.get_connector_properties(ROOT_HELPER, None, False, False)

    # Call out to the driver's initialize_connection to get connection_info.
    connection_info = cinder.volumes.initialize_connection(FC_VOL, connector_props)

    # Calling get_volume_luns
    payload = {'volume': FC_VOL,
               'connection_info': connection_info,
               'root_helper': ROOT_HELPER}
    r = requests.post(FLASK_URL + "get_volume_luns", json=payload)
    result = r.json()
    print("\nExisting source luns:")
    pprint.pprint(result)

    # Calling get_all_luns
    all_luns = fetch_all_luns()
    print("\nAll source luns:")
    pprint.pprint(all_luns)

    print("--------------------")

def iscsi_test():
    print("\n---- Testing iSCSI ----")
    cinder = client.Client(USER, PASS, TENANT, AUTH_URL, service_type="volume")

    # Use os_brick to get needed connection properties.
    connector_props = connector.get_connector_properties(args.root_helper, None, False, False)

    # Call out to the driver's initialize_connection to get connection_info.
    connection_info = cinder.volumes.initialize_connection(ISCSI_VOL, connector_props)

    # Calling get_volume_luns
    payload = {'volume': ISCSI_VOL,
               'connection_info': connection_info,
               'root_helper': ROOT_HELPER}
    r = requests.post(FLASK_URL + "get_volume_luns", json=payload)
    result = r.json()
    print("\nExisting source luns:")
    pprint.pprint(result)

    # Calling get_all_luns
    all_luns = fetch_all_luns()
    print("\nAll source luns:")
    pprint.pprint(all_luns)

    print("-----------------------")

def fetch_all_luns():
    # Calling get_all_luns
    r = requests.get(FLASK_URL + "get_all_luns")
    result = r.json()
    return result

if __name__ == '__main__':
    all_luns = fetch_all_luns()
    print("\nAll source luns:")
    pprint.pprint(all_luns)

    fc_test()
    iscsi_test()