# apg-pycis

## Overview

Python scripts, which support the Jenkins/Maven/Gradle CI Process (Apg Python CI Scripts)

TODO Overview of functionalty

## Installing

Preconditions: Valid Python installation

### As Package

Install the Python Script Packages from Git:

`'python -m pip install git+https://github.com/chhex/apg-pycis.git'`

If Python versions are controlled with pyenv:

`pyenv rehash`

There are currently the following 4 scripts avaibable:

jviewcopy , see TODO more detailed description
jviewscan , see TODO more detailed description
build_all , see TODO more detailed description
rdircopy , see TODO more detailed description 

To print out help, for example:

`jviewscan --help`

Example:

`jviewscan -s com.teamdev.jxbrowser  -v "Framework Builds" -f "Forms2Java Version Java8Mig 5.x"`

## Development

The following process is suggested:

clone from Git:

`git clone https://github.com/chhex/apg-pycis.git`

Open the repository in your IDE, which supports Python.

For local testing, cd the repo directory:

```python
pip install --editable .
source .venv/bin/activate
pip install --editable .
```

Maybe you need to upgrade pip: `pip install --upgrade pip`

To check the installation: `which jviewcopy`

It should point to `<repo_path>/.venv/bin/jviewcopy`

To publish the packages, bump the version in pyproject.toml and commit and push the changes.


## Open Issues

