# apg-pycis

## Overview

Python scripts, which support the Jenkins/Maven/Gradle CI Process (Apg Python CI Scripts)

TODO Overview of functionalty

## Installing

Preconditions: Valid Python installation
Install the Python Package from Git:

`python -m pip install git+https://github.com/chhex/apg-pycis.git`

If Python versions are controlled with pyenv:

`pyenv rehash`


To print out help:

`jviewscan --help`

Example for non interactive modus:

`jviewscan -s com.teamdev.jxbrowser  -v "Framework Builds" -f "Forms2Java Version Java8Mig 5.x"`

## Development

TODO Describe development process

## Open Issues

- Support SOURCE and TARGET jenkins URI and PORT in configuration, for example copy from one jenkins instance to another 
- Support Multiple Views as Source
- For interactive modus add colors, to support a better visibilty and seperation of concerns

