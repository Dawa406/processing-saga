# -*- coding: utf-8 -*-

"""
***************************************************************************
    sagaUtils.py
    ---------------------
    Date                 : February 2018
    Copyright            : (C) 2018 by Alexander Bruy
    Email                : alexander dot bruy at gmail dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Alexander Bruy'
__date__ = 'February 2018'
__copyright__ = '(C) 2018, Alexander Bruy'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import os
import re
import subprocess

from qgis.core import QgsMessageLog, QgsProcessingFeedback
from processing.core.ProcessingLog import ProcessingLog
from processing.core.ProcessingConfig import ProcessingConfig

versionRegex = re.compile("([\d.]+)")

SAGA_ACTIVE = "SAGA_ACTIVE"
SAGA_EXECUTABLE = "SAGA_EXECUTABLE"
SAGA_VERBOSE = "SAGA_VERBOSE"


def sagaExecutable():
    filePath = ProcessingConfig.getSetting(SAGA_EXECUTABLE)
    return filePath if filePath is not None else ""


def descriptionPath():
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "descriptions"))


def version():
    commands = sagaExecutable()
    if commands == "":
        commands = "saga_cmd"
    commands += " --version"

    with subprocess.Popen([commands],
                          shell=True,
                          stdout=subprocess.PIPE,
                          stdin=subprocess.DEVNULL,
                          stderr=subprocess.STDOUT,
                          universal_newlines=True) as proc:
        try:
            for line in proc.stdout:
                if line.startswith("SAGA"):
                    return versionRegex.search(line.strip()).group(0)
            return None
        except:
            return None


def execute(commands, feedback=None):
    if feedback is None:
        feedback = QgsProcessingFeedback()

    fused_command = " ".join([str(c) for c in commands])
    QgsMessageLog.logMessage(fused_command, "Processing", QgsMessageLog.INFO)
    feedback.pushInfo("SAGA command:")
    feedback.pushCommandInfo(fused_command)
    feedback.pushInfo("SAGA command output:")

    loglines = []
    with subprocess.Popen(fused_command,
                          shell=True,
                          stdout=subprocess.PIPE,
                          stdin=subprocess.DEVNULL,
                          stderr=subprocess.STDOUT,
                          universal_newlines=True) as proc:
        try:
            for line in iter(proc.stdout.readline, ""):
                feedback.pushConsoleInfo(line)
                loglines.append(line)
        except:
            pass

    if ProcessingConfig.getSetting(SAGA_VERBOSE):
        QgsMessageLog.logMessage("\n".join(loglines), "Processing", QgsMessageLog.INFO)
