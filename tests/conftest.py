import os

import pytest

from sigmabam2openbis.parser import SigmaBAM2OpenBISParser

if os.getenv("_PYTEST_RAISE", "0") != "0":

    @pytest.hookimpl(tryfirst=True)
    def pytest_exception_interact(call):
        raise call.excinfo.value

    @pytest.hookimpl(tryfirst=True)
    def pytest_internalerror(excinfo):
        raise excinfo.value


@pytest.fixture(scope="module")
def parser():
    return SigmaBAM2OpenBISParser()
