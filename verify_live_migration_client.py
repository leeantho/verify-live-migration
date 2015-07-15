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

import argparse
import pprint
import requests
import os
import json

def fetch_volume_luns(flask_url, volume_id):
    """
    Queries for a specific volume's luns.

    Precondition:
    Volume is attached to an instance.
    """
    # Calling get_volume_luns
    payload = {'volume_id': volume_id}
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
    parser.add_argument("-ip", help="ip of flask server", default="localhost")
    parser.add_argument("-port", help="port of flask server", default=5002, type=int)
    parser.add_argument("-v", "--volume-id", help="volume id", required=True)
    args = parser.parse_args()

    flask_url = "http://%s:%s/" % (args.ip, args.port)

    all_luns = fetch_all_luns(flask_url)
    print("\nAll source luns:")
    pprint.pprint(all_luns)

    volume_luns = fetch_volume_luns(flask_url,
                                    args.volume_id)
    print("\nExisting source luns:")
    pprint.pprint(volume_luns)
