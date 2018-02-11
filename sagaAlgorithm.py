# -*- coding: utf-8 -*-

"""
***************************************************************************
    sagaAlgorithm.py
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

from qgis.PyQt.QtGui import QIcon
from qgis.core import (QgsProcessing,
                       QgsProcessingUtils,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterRange,
                       QgsProcessingParameterExtent,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterString,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterMultipleLayers,
                       QgsProcessingParameterFileDestination,
                       QgsProcessingParameterFolderDestination,
                       QgsProcessingParameterRasterDestination,
                       QgsProcessingParameterVectorDestination
                      )
from processing.core.ProcessingConfig import ProcessingConfig
from processing.core.parameters import getParameterFromString

from processing_saga import sagaUtils

pluginPath = os.path.dirname(__file__)

sessionRasters = dict()
validChars = re.compile(r"[^A-Za-z0-9]+")


class SagaAlgorithm(QgsProcessingAlgorithm):

    OUTPUT_EXTENT = "OUTPUT_EXTENT"

    def __init__(self, descriptionFile):
        super().__init__()

        self.descriptionFile = descriptionFile
        self._name = ""
        self._displayName = ""
        self._group = ""
        self._groupId = ""
        self._shortHelp = ""

        self.params = []

        self.rasters = []
        self.extentParams = []

        self.defineCharacteristicsFromFile()

    def createInstance(self):
        return self.__class__(self.descriptionFile)

    def name(self):
        return self._name

    def displayName(self):
        return self._displayName

    def group(self):
        return self._group

    def groupId(self):
        return self._groupId

    def shortHelpString(self):
        return self._shortHelp

    def icon(self):
        return QIcon(os.path.join(pluginPath, "icons", "saga.svg"))

    def tr(self, text):
        return QCoreApplication.translate("SagaAlgorithm", text)

    def initAlgorithm(self, config=None):
        for p in self.params:
            self.addParameter(p, True)

            # TODO: file destinations are not automatically added as outputs

    def defineCharacteristicsFromFile(self):
        with open(self.descriptionFile) as lines:
            line = lines.readline().strip()
            self._name = line
            self._displayName = line

            line = lines.readline().strip()
            self._groupId = line

            line = lines.readline().strip()
            self._group = line

            #line = lines.readline().strip("\n").strip()
            #self._shortHelp = line

            line = lines.readline().strip()
            while line != '':
                if line.startswith("QgsProcessingParameterExtent"):
                    self.extentParams = line.split("|")[1].split(";")
                    self.params.append(QgsProcessingParameterExtent(self.OUTPUT_EXTENT, "Extent"))
                else:
                    self.params.append(getParameterFromString(line))

                line = lines.readline().strip("\n").strip()

    def checkParameterValues(self, parameters, context):
        rasters = []
        for param in self.parameterDefinitions():
            if isinstance(param, QgsProcessingParameterRasterLayer):
                if parameters[param.name()]:
                    rasters.append(parameters[param.name()])
            elif isinstance(param, QgsProcessingParameterMultipleLayers) and param.layerType() == QgsProcessing.TypeRaster:
                if parameters[param.name()]:
                    layers.extend(parameters[param.name()])

        dimensions = None
        for raster in rasters:
            if raster is None or raster == "":
                continue

            if raster.bandCount() > 1:
                return False, self.tr("Input layer {} is a multiband raster.").format(raster.name())

            if dimensions is None:
                dimensions = [raster.extent(), raster.height(), raster.width()]
            else:
                if dimensions != [raster.extent(), raster.height(), raster.width()]:
                    return False, self.tr("Input layers have different grid extents.")

        return super(SagaAlgorithm, self).checkParameterValues(parameters, context)

    def exportRaster(self, parameters, name, context):
        layer = self.parameterAsRasterLayer(parameters, name, context)

        global sessionRasters
        if layer.source() in sessionRasters:
            exported = sessionRasters[layer.source()]
            if os.path.exists(exported):
                self.rasters[name] = exported
                return None
            else:
                del sessionRasters[layer.source()]

        rasterName = os.path.splitext(os.path.basename(layer.source()))[0]
        rasterName = validChars.sub(fileName, "")
        if rasterName == "":
            rasterName = "raster"

        fileName = QgsProcessingUtils.generateTempFilename("{}.sgrd".format(rasterName))
        sessionRasters[layer.source()] = fileName
        self.rasters[name] = fileName

        cmd = self.provider().exportCommand
        resampling = ProcessingConfig.getSetting(sagaUtils.SAGA_RESAMPLING)

        return cmd.format(resampling, filename, layer.source())

    def processAlgorithm(self, parameters, context, feedback):
        pass
