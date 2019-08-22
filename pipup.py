# pipup - jkindall@ - 2019-08-21
# updates installed modules that have available updates

# Usage:
# python pipup.py [partialname]
#
# updates oudated modules whose name contains partialname, or
# all outdated modules if partialname is not supplied

# Example: python pipup.py aws-cdk
# Updates all installed AWS Cloud Development Kit modules
# but not other outdated modules

from pip._internal import main as pip
from io import StringIO
import sys

partialname = "" if len(sys.argv) < 2 else sys.argv[1]

class stdout(list):
    """Context manager to capture lines from stdout as a list"""
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stdout = self._stdout

# get list outdated modules (and their current versions)
with stdout() as modules:
    pip(["list", "--outdated", "--format=freeze"])

# for each outdated module, call pip install --upgrade
for module in modules:
    name, _, _ = module.partition("==")
    if partialname in name:
        pip(["install", "--upgrade", name])
