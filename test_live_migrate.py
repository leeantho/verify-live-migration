"""
test_live_migrate.py

Description:
    A sample implementation using the novaclient and live migration verification
    scripts to test a simple live migration scenario. The scenario being tested
    live migrates an instance with one volume attached between two hosts n number
    of times.

    ** Important **
    Make sure the instance is located on the first host before beginning the test.

Usage:
    # Start the first flask server API.
    python verify_live_migration.py
    # Start the second flask server API.
    python verify_live_migration.py
    # Run the client, specifying all required arguments and optional arguments as needed.
    python test_live_migrate.py -ip1 99.99.999.999 -h1 sample_host1 -ip2 99.99.999.999 -h2 sample_host2 -v 50bceb5d-b6ed-4c04-818e-785acfede07c -s 9907efed-6eb4-4cc3-a03d-08d489a8d07a
"""
from novaclient import client as nova_client
import verify_live_migration_client

import argparse
import os
import pprint
import time

def test_live_migration(username, password, tenant, auth, flask_url_a, flask_url_b, host_a, host_b, server_id, vol_ids, runs):
    success = 0
    fail = 0
    print("DOING %s RUNS" % runs)
    for attempt in range(0, runs):
        print("\nATTEMPT %s START" % (attempt + 1))
        dest_host = ""
        src_flask = ""

        # Toggle for migrating instances back and forth between hosts.
        if attempt % 2 == 0:
            dest_host = host_b
            src_flask = flask_url_a
        else:
            dest_host = host_a
            src_flask = flask_url_b

        # Collect a list of all the volume luns on the source.
        vol_id_list = vol_ids.split(',')
        vol_luns = []
        for vol_id in vol_id_list:
            luns = verify_live_migration_client.fetch_volume_luns(src_flask, vol_id)
            for lun in luns:
                if lun not in vol_luns:
                    vol_luns.append(lun)
        print("Volume luns on source node:")
        pprint.pprint(vol_luns)

        print("live-migrate to %s" % dest_host)
        _do_live_migrate(username, password, tenant, auth, dest_host, server_id)

        all_luns = verify_live_migration_client.fetch_all_luns(src_flask)
        print("all luns on source node after live migration:")
        pprint.pprint(all_luns)

        # Check that all the volume luns on the source are gone.
        vol_lun_present = False
        for lun in vol_luns:
            if lun in all_luns:
                vol_lun_present = True
                break
        if vol_lun_present:
            print("FAIL")
            fail += 1
        else:
            print("SUCCESS")
            success += 1
        print("ATTEMPT %s END" % (attempt + 1))

    print("\nTotal runs: %s" % runs)
    print("Total success: %s" % success)
    print("Total fail: %s" % fail)

def _do_live_migrate(username, password, tenant, auth, dest_host, server_id):
    print("Starting Live Migration to %s." % dest_host)
    nova = nova_client.Client(2, username, password, tenant, auth)
    nova.servers.live_migrate(server_id, dest_host, False, False)
    server = nova.servers.get(server_id)
    while server.status != "ACTIVE":
        server = nova.servers.get(server_id)
        time.sleep(0.1)

    print("Live Migration to %s done." % dest_host)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-username", help="username", default=os.environ['OS_USERNAME'])
    parser.add_argument("-password", help="password", default=os.environ['OS_PASSWORD'])
    parser.add_argument("-tenant", help="tenant name", default=os.environ['OS_TENANT_NAME'])
    parser.add_argument("-auth", help="auth url", default=os.environ['OS_AUTH_URL'])
    parser.add_argument("-root-helper", help="root helper", default="sudo")
    parser.add_argument("-ip1", help="ip of first flask server", required=True)
    parser.add_argument("-ip2", help="ip of second flask server", required=True)
    parser.add_argument("-port1", help="port of first flask server", default=5002, type=int)
    parser.add_argument("-port2", help="port of second flask server", default=5002, type=int)
    parser.add_argument("-v", "--volume-ids", help="volume ids, comma separated", required=True)
    parser.add_argument("-s", "--server-id", help="server id", required=True)
    parser.add_argument("-r", "--runs", help="number of times to perform live migration", default=2, type=int)
    parser.add_argument("-h1", "--host1", help="name of the first host", required=True)
    parser.add_argument("-h2", "--host2", help="name of the second host", required=True)
    args = parser.parse_args()

    flask_url1 = "http://%s:%s/" % (args.ip1, args.port1)
    flask_url2 = "http://%s:%s/" % (args.ip2, args.port2)

    test_live_migration(args.username,
                        args.password,
                        args.tenant,
                        args.auth,
                        flask_url1,
                        flask_url2,
                        args.host1,
                        args.host2,
                        args.server_id,
                        args.volume_ids,
                        args.runs)
