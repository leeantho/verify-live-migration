# verify-live-migration
Script for automating live-migration testing between a controller and compute node.

Documentation for usage is in the files currently.

Flask servers must be started on the controller and compute nodes.

Run the test_live_migrate script with needed inputs to start automated live-migration.


SETUP
=====
Install verify_live_migration.py on each of the compute hosts,
and then launch them. 

The test_live_migrate.py and verify_live_migration_client.py
live on the same host that initiates the tests.

Make sure you can ping both of the compute hosts from the machine you run
the test_live_migrate.py script.
