import argparse
import logging
import os
import paramiko
import sys
import time

import brick_cinderclient_ext
from novaclient import client

LOG = logging.getLogger('__name__')
LOG.propagate = False
file_handler = logging.FileHandler("output.log")
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
file_handler.setFormatter(formatter)
LOG.addHandler(file_handler)

stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.DEBUG)
stdout_handler.setFormatter(formatter)
LOG.addHandler(stdout_handler)
stdout_handler.setFormatter(formatter)
LOG.setLevel(logging.DEBUG)

nova_client = None

def run_live_migration(test_env):
    success = 0
    fail = 0

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    export_cmd = "export OS_USERNAME=%s; export OS_PASSWORD=%s; export OS_AUTH_URL=%s; export OS_TENANT_NAME=%s;" % (test_env['username'], test_env['password'], test_env['auth_url'], test_env['tenant'])

    LOG.info("Running live migration between targets (%s runs)" % test_env['runs'])
    for attempt in range(0, test_env['runs']):
        LOG.info("START RUN #%s" % str(attempt + 1))
        # Determine which host is source and destination
        src, dest = _determine_source_and_dest(test_env['target_a'], test_env['target_b'], attempt)
        # Do a precheck of volume paths
        vol_paths_pre_migrate = []
        for volume in test_env['volume_ids']:
            try:
                ssh.connect(hostname=src['host'], username=src['username'], password=src['password'])
                cmd = export_cmd + " cinder get-volume-paths %s" % volume
                if test_env['use_multipath']:
                    cmd += " --multipath"
                stdin, stdout, stderr = ssh.exec_command(cmd)
                vol_paths = stdout.read().strip().split()
                for path in vol_paths:
                    if path not in vol_paths_pre_migrate:
                        vol_paths_pre_migrate.append(path)
            finally:
                ssh.close()
        LOG.info("vol_paths_pre_migrate: %s" % vol_paths_pre_migrate)
        # Do the live migration
        LOG.info("Doing live migration from %s to %s" % (src['host'], dest['host']))
        _do_live_migration(test_env['server_id'], dest)
        # Do a postcheck of volume paths
        all_vol_paths_post_migrate = []
        try:
            ssh.connect(hostname=src['host'], username=src['username'], password=src['password'])
            stdin, stdout, stderr = ssh.exec_command(export_cmd + " cinder get-all-volume-paths --multipath %s" % test_env['use_multipath'])
            all_vol_paths_post_migrate = stdout.read().strip().split()
        finally:
            ssh.close()
        LOG.info("all_vol_paths_post_migrate: %s" % all_vol_paths_post_migrate)
        # Determine if a success or fail occured
        vol_path_present = _are_vol_paths_present(vol_paths_pre_migrate, all_vol_paths_post_migrate)
        if vol_path_present:
            LOG.info("FAIL")
            fail += 1
        else:
            LOG.info("SUCCESS")
            success += 1
        LOG.info("FINISHED RUN #%s" % str(attempt + 1))

    LOG.info("success: %s" % success)
    LOG.info("fail: %s" % fail)        
        
def _are_vol_paths_present(vol_paths, all_vol_paths):
    vol_path_present = False
    for path in vol_paths:
        if path in all_vol_paths:
            vol_path_present = True
            break
    return vol_path_present

def _determine_source_and_dest(target_a, target_b, attempt):
    src = ""
    dest = ""

    # Toggle src and dest based on even or odd attempt number
    if attempt % 2 == 0:
        dest = target_b
        src = target_a
    else:
        dest = target_a
        src = target_b

    return src, dest

def _do_live_migration(server_id, dest):
    nova_client.servers.live_migrate(server_id, dest['host'], False, False)
    server = nova_client.servers.get(server_id)
    while server.status != "ACTIVE":
        server = nova_client.servers.get(server_id)
        time.sleep(0.1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", help="username", default=os.environ['OS_USERNAME'])
    parser.add_argument("-p", "--password", help="password", default=os.environ['OS_PASSWORD'])
    parser.add_argument("-t", "--tenant", help="tenant", default=os.environ['OS_TENANT_NAME'])
    parser.add_argument("-a", "--auth", help="auth url", default=os.environ['OS_AUTH_URL'])
    parser.add_argument("-h1", "--host1", help="name of the first host", required=True)
    parser.add_argument("-h1u", "--host1-user", help="user for the first host", required=True)
    parser.add_argument("-h1p", "--host1-password", help="password for the first host", required=True)
    parser.add_argument("-h2", "--host2", help="name of the second host", required=True)
    parser.add_argument("-h2u", "--host2-user", help="user for the second host", required=True)
    parser.add_argument("-h2p", "--host2-password", help="password for the second host", required=True)
    parser.add_argument("-r", "--runs", help="number of runs to do", type=int, default=2)
    parser.add_argument("-m", "--multipath", help="use multipath", action="store_true", default=False)
    parser.add_argument("-s", "--server-id", help="server id", required=True)
    parser.add_argument("-v", "--volume-ids", help="volume ids, comma separated", required=True)
    args = parser.parse_args()

    nova_client = client.Client(2, args.username, args.password, args.tenant, args.auth)
    target_a = {"host": args.host1, "username": args.host1_user, "password": args.host1_password}
    target_b = {"host": args.host2, "username": args.host2_user, "password": args.host2_password}
    volume_ids = args.volume_ids.split(',')
    test_env = {
        "target_a": target_a,
        "target_b": target_b,
        "volume_ids": volume_ids,
        "server_id": args.server_id,
        "use_multipath": args.multipath,
        "runs": args.runs,
        "username": args.username,
        "password": args.password,
        "tenant": args.tenant,
        "auth_url": args.auth,
    }

    run_live_migration(test_env)
