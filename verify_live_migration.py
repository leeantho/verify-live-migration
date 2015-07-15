"""
verify_live_migration.py

Description:
    Provides two APIs via a Flask server so that either all luns on the system
    can be retrieved or only luns for a specific volume.

Usage:
    # start the flask server (optionally, define port for the server)
    python verify_live_migration.py -port 5005
    # using an external client call either of the APIs
"""
from os_brick.initiator import connector
from os_brick.initiator import linuxfc
from cinderclient.v2 import client

import argparse
import os
import subprocess
import json

from flask import Flask, make_response, request

parser = argparse.ArgumentParser()
parser.add_argument("-username", help="username", default=os.environ['OS_USERNAME'])
parser.add_argument("-password", help="password", default=os.environ['OS_PASSWORD'])
parser.add_argument("-tenant", help="tenant name", default=os.environ['OS_TENANT_NAME'])
parser.add_argument("-auth", help="auth url", default=os.environ['OS_AUTH_URL'])
parser.add_argument("-root-helper", help="root helper", default="sudo")
parser.add_argument("-port", help="port that flask server will use.", default=5002, type=int)
parser.add_argument("-debug", help="enable debugging.", default=False, action="store_true")
args = parser.parse_args()

app = Flask(__name__)

USERNAME = args.username
PASSWORD = args.password
TENANT = args.tenant
AUTH = args.auth
ROOT_HELPER = args.root_helper

@app.route('/get_volume_luns', methods=['POST'])
def get_volume_luns():
    """
    Gets a specific volume's luns.

    Using a POST request volume, connection_info and root_helper must be sent.
    """
    print("Doing some pre-verification...")

    data = json.loads(request.data)
    volume_id = data['volume_id']

    cinder = client.Client(USERNAME, PASSWORD, TENANT, AUTH, service_type="volume")

    # Use os_brick to get needed connection properties.
    connector_props = connector.get_connector_properties(ROOT_HELPER, None, False, False)

    # Call out to the driver's initialize_connection to get connection_info.
    connection_info = cinder.volumes.initialize_connection(volume_id, connector_props)

    # Use os_brick to get possible devices.
    devices = []
    volume_type = connection_info['driver_volume_type']
    if volume_type == 'fibre_channel':
        print("FC detected.")
        linux_fc = linuxfc.LinuxFibreChannel(ROOT_HELPER)
        hbas = linux_fc.get_fc_hbas_info()
        ports = connection_info['data']['target_wwn']
        fc_conn = connector.FibreChannelConnector(ROOT_HELPER)

        possible_devs = fc_conn._get_possible_devices(hbas, ports)
        lun = connection_info['data'].get('target_lun', 0)
        devices = fc_conn._get_host_devices(possible_devs, lun)
    elif volume_type == 'iscsi':
        print("iSCSI detected")
        iscsi_conn = connector.ISCSIConnector(ROOT_HELPER)
        devices = iscsi_conn._get_device_path(connection_info['data'])

    # Filter possible devices based on luns in /dev/disk/by-path
    dev_bypath = get_dev_disk_bypath()
    output = []
    for dev in dev_bypath:
        for p_dev in devices:
           if dev in p_dev:
               output.append(dev)

    print("Pre-verification done.")
    resp = make_response(json.dumps(output), 200)
    return resp

@app.route('/get_all_luns', methods=['GET'])
def get_all_luns():
    """
    Gets all luns on the system (from /dev/disk/by-path).
    """
    print("Get all luns...")
    print("Done getting all luns.")
    devices = get_dev_disk_bypath()
    resp = make_response(json.dumps(devices), 200)
    return resp

def get_dev_disk_bypath():
    print("Getting /dev/disk/by-path output...")

    p = subprocess.Popen(['ls', '/dev/disk/by-path'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = p.communicate()
    output = out[0].strip().split('\n')

    print("Done getting /dev/disk/by-path output.")
    return output

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=args.debug, port=args.port)
