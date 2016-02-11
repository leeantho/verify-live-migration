Pre-Requisites
==============

os-brick -- https://github.com/openstack/os-brick (pull latest master)

python-brick-cinderclient-ext -- https://github.com/openstack/python-brick-cinderclient-ext

The following patch needs to pulled into the python-brick-cinderclient-ext:
https://review.openstack.org/#/c/268405/

Setup
=====

When running the script make sure the OS_AUTH_URL environment variable uses the
IP of the compute-host (parent node) instead of localhost.
