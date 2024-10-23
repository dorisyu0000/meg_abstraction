#!/usr/bin/env python
# -*- coding: utf-8 -*-

# instead of import *, use this (+ PSYCHOPY_USERAGENT if you need that)
# (NOT_STARTED, STARTED, PLAYING, PAUSED, STOPPED, FINISHED, PRESSED,
#  RELEASED, FOREVER)

import sys, os, copy
from os.path import abspath, join
from types import SimpleNamespace

# pertaining to the status of components/routines/experiments
status = SimpleNamespace()
status.__doc__ = (
    "- NOT_STARTED (0): The component has not yet started.\n"
    "- PLAYING / STARTED (1): The component has started.\n"
    "- PAUSED (2): The component has started but has been paused.\n"
    "- RECORDING (3): Component is not only started, but also actively recording some input.\n"
    "- STOPPED / FINISHED (-1): Component has finished.\n"
    "- SKIP / SEEKING (-2): Component is in the process of changing state.\n"
    "- STOPPING (-3): Component is in the process of stopping.\n"
    "- INVALID (-9999): Something has gone wrong and status is not available.\n"
)
status.NOT_STARTED = NOT_STARTED = 0
status.PLAYING = PLAYING = 1
status.STARTED = STARTED = PLAYING
status.PAUSED = PAUSED = 2
status.RECORDING = RECORDING = 3
status.STOPPED = STOPPED = -1
status.FINISHED = FINISHED = STOPPED
status.SKIP = SKIP = SEEKING = -2
status.STOPPING = STOPPING = -3
status.INVALID = INVALID = -9999

# pertaining to the priority of columns in the data file
priority = SimpleNamespace()
priority.__doc__ = (
    "- CRITICAL (30): Always at the start of the data file, generally reserved for Routine start times\n "
    "- HIGH (20): Important columns which are near the front of the data file\n"
    "- MEDIUM (10): Possibly important columns which are around the middle of the data file\n"
    "- LOW (0): Columns unlikely to be important which are at the end of the data file\n"
    "- EXCLUDE (-10): Always at the end of the data file, actively marked as unimportant\n"
)
priority.CRITICAL = PRIORITY_CRITICAL = 30
priority.HIGH = PRIORITY_HIGH = 20
priority.MEDIUM = PRIORITY_MEDIUM = 10
priority.LOW = PRIORITY_LOW = 0
priority.EXCLUDE = PRIORITY_EXCLUDE = -10

# for button box:
PRESSED = 1
RELEASED = -1

# while t < FOREVER ... -- in scripts generated by Builder
FOREVER = 1000000000  # seconds

# USERAGENT is for consistent http-related self-identification across an app.
# It shows up in server logs on the receiving end. Currently, the value (and
# its use from psychopy) is arbitrary and optional. Having it standardized
# and fixed will also help people who develop their own http-log analysis
# tools for use with contrib.http.upload()
PSYCHOPY_USERAGENT = ("PsychoPy: open-source Psychology & Neuroscience tools; "
                      "www.psychopy.org")


# find a copy of git if possible to do push/pull as needed
# the pure-python dulwich lib can do most things but merged push/pull
# isn't currently possible (e.g. pull overwrites any local commits!)
# see https://github.com/dulwich/dulwich/issues/666
ENVIRON = copy.copy(os.environ)
gitExe = None
if sys.platform == 'darwin':
    _gitStandalonePath = abspath(join(sys.executable, '..', '..',
                                      'Resources', 'git-core'))
    if os.path.exists(_gitStandalonePath):
        ENVIRON["PATH"] = "{}:".format(_gitStandalonePath) + ENVIRON["PATH"]
        gitExe = join(_gitStandalonePath, 'git')

elif sys.platform == 'win32':
    _gitStandalonePath = abspath(join(sys.executable, '..', 'MinGit', 'cmd'))
    if os.path.exists(_gitStandalonePath):
        ENVIRON["PATH"] = "{};".format(_gitStandalonePath) + ENVIRON["PATH"]
        os.environ["GIT_PYTHON_GIT_EXECUTABLE"] = _gitStandalonePath
        gitExe = join(_gitStandalonePath, 'git.exe')

if gitExe:
    os.environ["GIT_PYTHON_GIT_EXECUTABLE"] = gitExe