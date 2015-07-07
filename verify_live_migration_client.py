"""
verify_live_migration_client.py

Description:
    A sample client that interacts with and tests the verify_live_migration
    flask server.

Usage:
    # Start the flask server API.
    python verify_live_migration.py -port 5005
    # Run the client, specifying volume_id and optional arguments as needed.
    python verify_live_migration_client.py -v 12345 -port 5005
"""
from os_brick.initiator import connector
from cinderclient.v2 import client

import argparse
import pprint
import requests
import os
import json

def fetch_volume_luns(username, password, tenant, auth, root_helper, flask_url, volume_id):
    """
    Queries for a specific volume's luns.

    Precondition:
    Volume is attached to an instance.
    """
    cinder = client.Client(username, password, tenant, auth, service_type="volume")

    # Use os_brick to get needed connection properties.
    connector_props = connector.get_connector_properties(root_helper, None, False, False)

    # Call out to the driver's initialize_connection to get connection_info.
    connection_info = cinder.volumes.initialize_connection(volume_id, connector_props)

    # Calling get_volume_luns
    payload = {'volume': volume_id,
               'connection_info': connection_info,
               'root_helper': root_helper}
    r = requests.post(flask_url + "get_volume_luns", json=payload)
    result = r.json()

    return result

def fetch_all_luns(flask_url):
    """
    Queries all luns on a system.
    """
    r = requests.get(flask_url + "get_all_luns")
    result = r.json()
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-username", help="username", default=os.environ['OS_USERNAME'])
    parser.add_argument("-password", help="password", default=os.environ['OS_PASSWORD'])
    parser.add_argument("-tenant", help="tenant name", default=os.environ['OS_TENANT_NAME'])
    parser.add_argument("-auth", help="auth url", default=os.environ['OS_AUTH_URL'])
    parser.add_argument("-root-helper", help="root helper", default="sudo")
    parser.add_argument("-ip", help="ip of flask server", default="localhost")
    parser.add_argument("-port", help="port of flask server", default=5002, type=int)
    parser.add_argument("-v", "--volume-id", help="volume id", required=True)
    args = parser.parse_args()

    flask_url = "http://%s:%s/" % (args.ip, args.port)

    all_luns = fetch_all_luns(flask_url)
    print("\nAll source luns:")
    pprint.pprint(all_luns)

    volume_luns = fetch_volume_luns(args.username,
                                    args.password,
                                    args.tenant,
                                    args.auth,
                                    args.root_helper,
                                    flask_url,
                                    args.volume_id)
    print("\nExisting source luns:")
    pprint.pprint(volume_luns)