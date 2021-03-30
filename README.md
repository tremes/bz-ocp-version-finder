# bz-ocp-version-finder
Tries to find and print released OCP versions for OCP Bugzilla issues

# Install dependencies
Install dependencies with:

`pip install -r requirements.txt`

The `gssapi` dependency requires `krb5-devel` library installed on your system.

# How to run
This script needs to authenticate to Bugzilla instance and RH errata tool. You need to provide your Bugzilla username/password 
and have valid kerberos ticket to be able to access the errata tool:

`python3 get_ocp_versions.py -u <username> -p <password>`

Optionally you can provide OCP version (default is `4.8`) to limit the Bugzillas you are looking for:

`python3 get_ocp_versions.py -u <username> -p <password> -v 4.6`