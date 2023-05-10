import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.joinpath("src")))

from curricularanalytics import Curriculum, read_csv


curr = read_csv("../ExploratoryCurricularAnalytics/files/Curriculum-CS26.csv")
assert isinstance(curr, Curriculum)
print(curr.basic_metrics().getvalue())
