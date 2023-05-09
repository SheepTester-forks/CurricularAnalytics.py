# https://github.com/tomchen/example_pypi_package/issues/1#issuecomment-1504300024
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.joinpath("src")))
