import pytest

from exposition.markdown import *


def test_header():
    assert Header('Some Text').write() == '# Some Text'
