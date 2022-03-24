# bz-ocp-version-finder
Tries to find and print released OCP versions for OCP Bugzilla issues

# Setup

 * Open https://errata.devel.redhat.com/ in a browser to verify that you have permissions to access the Errata Tool.

 * [Configure Kerberos and Red Hat IdM](https://source.redhat.com/groups/public/ccs-onboarding-program/ccs_onboarding_wiki/setting_up_a_kerberos_ticket_and_red_hat_idm)

 * Make sure that the `krb5-devel` package is installed on your system. Python's `gssapi` package needs it.
 
   ```$ sudo dnf instal krb5-devel```

 * Set up a Python virtual environment

   ```$ python -m venv path/to/your/venv```

 * Enter the virtual environment

   ```$ source path/to/your/venv/bin/activate```

 * Install dependencies

   ```$ pip install -r requirements.txt```


# Usage

 * Get a Kerberos ticket granting ticket for accessing the errata tool

   ```$ kinit username@REDHAT.COM```

 * Run the script with your Bugzilla key

   ```$ python3 get_ocp_versions.py -t <bugzilla_key>```

 * Optionally you can provide OCP version (default is `4.8`) to limit the Bugzillas you are looking for:

   ```$ python3 get_ocp_versions.py -t <bugzilla_key> -v 4.6```
