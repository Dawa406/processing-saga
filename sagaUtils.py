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
import stat
import tempfile
import subprocess

from qgis.core import Qgis, QgsMessageLog, QgsProcessingFeedback
from processing.core.ProcessingLog import ProcessingLog
from processing.core.ProcessingConfig import ProcessingConfig
from processing.tools.system import isWindows

versionRegex = re.compile("([\d.]+)")

SAGA_ACTIVE = "SAGA_ACTIVE"
SAGA_EXECUTABLE = "SAGA_EXECUTABLE"
SAGA_RESAMPLING = "SAGA_RESAMPLING"
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


def jobFile():
    if isWindows():
        fileName = "saga_job.bat"
    else:
        fileName = "saga_job.sh"

    return os.path.join(tempfile.gettempdir(), fileName)


def createJobFile(commands):
    #FIXME: set env variables
    with open(jobFile(), "w", encoding="utf-8") as f:
        for cmd in commands:
            f.write("saga_cmd -f=q {}\n".format(cmd))
        f.write("exit")


def execute(commands, feedback=None):
    if feedback is None:
        feedback = QgsProcessingFeedback()

    createJobFile(commands)
    QgsMessageLog.logMessage("\n".join(commands), "Processing", Qgis.Info)
    feedback.pushInfo("SAGA commands:")
    feedback.pushCommandInfo("\n".join(commands))

    if isWindows():
        commands = ["cmd.exe", "/C", jobFile()]
    else:
        os.chmod(jobFile(), stat.S_IEXEC | stat.S_IREAD | stat.S_IWRITE)
        commands = [jobFile()]

    fused_command = " ".join([str(c) for c in commands])
    QgsMessageLog.logMessage(fused_command, "Processing", Qgis.Info)
    feedback.pushInfo("SAGA job command:")
    feedback.pushCommandInfo(fused_command)
    feedback.pushInfo("SAGA commands output:")

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
        QgsMessageLog.logMessage("\n".join(loglines), "Processing", Qgis.Info)
