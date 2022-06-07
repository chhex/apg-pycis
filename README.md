# apg-pycis

## Overview

Python scripts, which support the Jenkins/Maven/Gradle CI Process (Apg Python CI Scripts)

Preconditions:
a The USER is a jenkins.apgsga.ch user
b The jenkins user needs to be able to access jenkins cli password less via ssh , see https://jenkins.apgsga.ch/cli/
c The jenkins userid is the same as the cvs.apgsga.ch user
d The cvs user has passwordless access to cvs.apgsga.ch

The script has a interactive and non interactive modus, see commandline option --not-interactive. The latter intended for automated processes.

The interfactive modus creates interactively a configuration file "config.ini" which is stored for later usage in `~/.apg_pycis`

The initial version of the config is taken from a template, which is distruted with the package.
Interactively one can stop the processing after the configuration file has been established.

The non interactive modus, presumes a valid `~/.apg_pycis/config.ini` file.

TODO Overview of functionalty

## Installing

Preconditions: Valid Python installation
Install the Python Package from Git:

`python -m pip install git+https://github.com/apgsga-it/apg-pycis.git`

If Python versions are controlled with pyenv:

`pyenv rehash`

For the interactive modus:

`jfuturbr`

To print out help:

`jfuturbr --help`

Example for non interactive modus:

`jfuturbr -ni --skip-commit --skip-create-jobs --skip-br`

## Open Issues

- Support SOURCE and TARGET jenkins URI and PORT in configuration, for example copy from one jenkins instance to another 
- Support Multiple Views as Source 

