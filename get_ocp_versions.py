r"""This scripts gets all the Bugzilla issues for given product,
component, version and status. Then it tries to find a Bugzilla comment
containing first mention of the corresponding Errata.
Finally it tries to read version ('[0-9]+\.[0-9]+\.[0-9]+')
from synopsis attribute of the Errata.
The script requires Bugzilla username and password arguments and you can execute as:

`python3 get_ocp_versions.py -u <username> -p <password>`

You can optionally provide an OCP version(default is `4.8`) like:

`python3 get_ocp_versions.py -u <username> -p <password> -v 4.6`

This script also requires active Kerberos ticket to be able to authorize to Erratum tool!
"""
import argparse
import json
import re
import warnings

import requests
from requests_gssapi import HTTPSPNEGOAuth

warnings.filterwarnings("ignore")


BUGZILLA_URL = "https://bugzilla.redhat.com/rest/"
PRODUCT = "OpenShift Container Platform"
COMPONENT = "Insights Operator"
ERRATA_API_URL = "https://errata.devel.redhat.com/api/v1/erratum/"


class BugzillaBug:
    def __init__(self, id, summary):
        self.id = id
        self.summary = summary


def bz_authenticate(user: str, password: str):
    r = requests.get(f"{BUGZILLA_URL}/login", params={"login": user, "password": password})

    json_data = r.json()
    if "token" not in json_data.keys():
        print("Can't read authorization token. Please try again!")
        return ""
    return json_data["token"]


"""
Fills the 'errata_bugs' dicitionary with errata-id -> [BugzillaBugs]
Iterates over the comments in the given bug and tries to find a comment from
'errata-xmlrpc@redhat.com' with text containing 'This bug has been added to advisory'.

Then it tries to parse the errata ID from this comment
"""


def create_errata_bz_bugs_mapping(bug: BugzillaBug, token: str):
    res = requests.get(f"{BUGZILLA_URL}/bug/{bug.id}/comment", params={"token": token})
    try:
        comments = res.json()
    except json.decoder.JSONDecodeError:
        print(f"can't decode comments in bug {bug.id}")
        return
    bug_data = comments["bugs"][str(bug.id)]
    for c in bug_data["comments"]:
        if (
            c["creator"] == "errata-xmlrpc@redhat.com"
            and "This bug has been added to advisory" in c["text"]
        ):
            ints = map(int, re.findall(r"\d+", c["text"]))
            errata_id = list(ints)[1]
            if errata_id in errata_bugs.keys():
                bugs = errata_bugs[errata_id]
                bugs.append(bug)
                errata_bugs.update({errata_id: bugs})
            else:
                errata_bugs[errata_id] = [bug]


def get_version_from_errata_synopsis(errata_id, auth):
    url = f"{ERRATA_API_URL}/{errata_id}.json"
    r = requests.get(url, auth=auth, verify=False)
    if not r.ok:
        if r.status_code == 401:
            print(
                f"Cannot access errata at {url}: {r.status_code} {r.reason}. "
                "Do you have a valid Kerberos TGT?"
            )
            return f"<unknown version>"
        else:
            print(
                f"Cannot access errata at {url}: {r.status_code} {r.reason}. "
                "Are you sure you have access?"
            )
            return f"<unknown version>"
    json_data = r.json()
    try:
        synopsis = json_data["errata"]["rhba"]["synopsis"]
    except KeyError as e:
        if e == "errata":
            print(f"can't read synopsis for errata id {errata_id}: {e}")
            return f"<unknown version> No synopsis in Errata {errata_id}"
        try:
            synopsis = json_data["errata"]["rhsa"]["synopsis"]
        except KeyError as e:
            print(f"can't read synopsis for errata id {errata_id}: {e}")
            return f"<unknown version> No synopsis in Errata {errata_id}"

    version = re.search(r"[0-9]+\.[0-9]+\.[0-9]+", synopsis)
    if version is None:
        return f"<unknown version> No version in Errata {errata_id} synopsis:{synopsis}"
    return version.group()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", help="Provide your Bugzilla user name")
    parser.add_argument("-p", help="Provide your Bugzilla password")
    parser.add_argument("-v", help="Provide component version")
    args = vars(parser.parse_args())

    if args["u"] is None:
        print("Please provide your Bugzilla username with -u")
        exit(1)
    if args["p"] is None:
        print("Please provide your Bugzilla password with -p")
        exit(1)

    user = args["u"]
    password = args["p"]
    version = args["v"] if args["v"] is not None else "4.8"

    token = bz_authenticate(user, password)
    if token == "":
        print("Bugzilla authentication was not successful!")
        exit(2)
    errata_neg_auth = HTTPSPNEGOAuth()
    errata_bugs = dict()

    # GET BUGS
    res = requests.get(
        f"{BUGZILLA_URL}/bug",
        params={
            "product": PRODUCT,
            "component": COMPONENT,
            "status": "CLOSED,VERIFIED",
            "version": version,
        },
    )
    all_bugs = res.json()

    # GET COMMENTS FOR EACH BUG
    for vb in all_bugs["bugs"]:
        bug_id = vb["id"]
        bug_summary = vb["summary"]
        bug = BugzillaBug(bug_id, bug_summary)
        create_errata_bz_bugs_mapping(bug, token)

    bugs_with_version = []
    # GET VERSION FROM ERRATA
    for errata_id, bugs in errata_bugs.items():
        version = get_version_from_errata_synopsis(errata_id, errata_neg_auth)
        for bug in bugs:
            if "unknown version" not in version:
                print(f"Bug {bug.id}: {bug.summary} Version: {version}")
