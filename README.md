# CurricularAnalytics.py

**CurricularAnalytics.py** is a toolbox for studying and analyzing academic program curricula. The toolbox represents curricula as graphs, allowing various graph-theoretic measures to be applied in order to quantify the complexity of curricula. In addition to analyzing curricular complexity, the toolbox supports the ability to visualize curricula, to compare and contrast curricula, to create optimal degree plans for completing curricula that satisfy particular constraints, and to simulate the impact of various events on student progression through a curriculum.

CurricularAnalytics.py is a Python port of the original Julia package [CurricularAnalytics.jl](https://github.com/CurricularAnalytics/CurricularAnalytics.jl).

## Documentation

Full documentation is available at [GitHub Pages](https://sheeptester-forks.github.io/CurricularAnalytics.py/).
Documentation for functions in this toolbox is also available via the Julia REPL help system.
Additional tutorials can be found at the [Curricular Analytics Notebooks](https://github.com/CurricularAnalytics/CA-Notebooks) site.

# Installation

Installation is straightforward. First, ensure you have Python 3.8 or higher installed. Then, run the following command.

```sh
# Linux/macOS
python3 -m pip install -U curricularanalytics

# Windows
py -3 -m pip install -U curricularanalytics
```

# Contributing and Reporting Bugs

We welcome contributions and bug reports! Please see [CONTRIBUTING.md](./CONTRIBUTING.md)
for guidance on development and bug reporting.

# Development

To build a distribution for upload to [PyPI](https://pypi.org/), run the following command.

```sh
rm -r dist
python -m build
python3 -m twine upload --repository testpypi dist/*
```

Learn more about [build and setuptools](https://setuptools.pypa.io/en/latest/userguide/quickstart.html).
