import sys

from configobj import ConfigObj

from coned_rtu import Coned

if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} <config file>")
    sys.exit(1)
config = ConfigObj(sys.argv[1])

CONED_USER = config.get("CONED_USER")
CONED_PASS = config.get("CONED_PASS")
CONED_TOTP = config.get("CONED_TOTP")
OPOWER_ACCOUNT_ID = config.get("OPOWER_ACCOUNT_ID")
OPOWER_METER = config.get("OPOWER_METER")
CONED_MAID = config.get("CONED_MAID")

coned = Coned(
    CONED_USER, CONED_PASS, CONED_TOTP, OPOWER_ACCOUNT_ID, OPOWER_METER, CONED_MAID
)

coned.login()
usage_json = coned.get_usage()
print(usage_json)
