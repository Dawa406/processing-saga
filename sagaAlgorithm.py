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
                       QgsProcessingParameterMatrix,
                       QgsProcessingParameterFeatureSource,
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

sessionLayers = dict()
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

        self.layers = {}
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
                    paramNames = line.split("|")[1].split(";")
                    if len(paramNames) == 4:
                        self.extentParams = paramNames
                    else:
                        for name in paramNames:
                            self.extentParams.append("{}_MIN".format(name))
                            self.extentParams.append("{}_MAX".format(name))
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
                return False, self.tr("Input layer '{}' is a multiband raster.").format(raster.name())

            if dimensions is None:
                dimensions = [raster.extent(), raster.height(), raster.width()]
            else:
                if dimensions != [raster.extent(), raster.height(), raster.width()]:
                    return False, self.tr("Input layers have different grid extents.")

        return super(SagaAlgorithm, self).checkParameterValues(parameters, context)

    def exportRaster(self, name, layer):
        global sessionLayers
        if layer.source() in sessionLayers:
            exported = sessionLayers[layer.source()]
            if os.path.exists(exported):
                self.layers[name] = exported
                return None
            else:
                del sessionLayers[layer.source()]

        rasterName = os.path.splitext(os.path.basename(layer.source()))[0]
        rasterName = validChars.sub(rasterName, "")
        if rasterName == "":
            rasterName = "exported"

        fileName = QgsProcessingUtils.generateTempFilename("{}.sgrd".format(rasterName))
        sessionLayers[layer.source()] = fileName
        self.layers[name] = fileName

        cmd = self.provider().exportCommand
        resampling = ProcessingConfig.getSetting(sagaUtils.SAGA_RESAMPLING)

        return cmd.format(resampling, fileName, layer.source())

    def convertLayers(self, parameters, context, feedback):
        commands = []

        for param in self.parameterDefinitions():
            if param.name() not in parameters or parameters[param.name()] is None:
                continue

            if isinstance(param, QgsProcessingParameterRasterLayer):
                layer = self.parameterAsRasterLayer(parameters, param.name(), context)

                if layer.source().lower().endswith("sdat"):
                    self.layers[param.name()] = "{}.sgrd".format(os.path.splitext(layer.source())[0])
                elif layer.source().lower().endswith("sgrd"):
                    self.layers[param.name()] = layer.source()
                else:
                    exportCommand = self.exportRaster(param.name(), layer)
                    if exportCommand is not None:
                        commands.append(exportCommand)
            elif isinstance(param, QgsProcessingParameterFeatureSource):
                filePath = self.parameterAsCompatibleSourceLayerPath(parameters, param.name(), context, ["shp"], "shp", feedback=feedback)
                if filePath:
                    self.layers[param.name()] = filePath
                else:
                    raise QgsProcessingException(self.tr("Input layer '{}' has unsupported format.".format(param.name())))
            elif isinstance(param, QgsProcessingParameterMultipleLayers):
                layers = self.parameterAsLayerList(parameters, param.name(), context)
                if layers is None or len(layers) == 0:
                    continue

                files = []
                if param.layerType() == QgsProcessing.TypeRaster:
                    for layer in layers:
                        if layer.source().lower().endswith("sdat"):
                            files.append("{}.sgrd".format(os.path.splitext(layer.source())[0]))
                        elif layer.source().lower().endswith("sgrd"):
                            files.append(layer.source())
                        else:
                            exportCommand = self.exportRaster(param.name(), layer)
                            files.append(self.layers[param.name()])
                            if exportCommand is not None:
                                commands.append(exportCommand)
                elif param.layerType() != QgsProcessing.TypeFile:
                    temp_params = deepcopy(parameters)
                    for layer in layers:
                        temp_params[param.name()] = layer

                        filePath = self.parameterAsCompatibleSourceLayerPath(temp_params, param.name(), context, ["shp"], "shp", feedback=feedback)
                        if filePath:
                            files.append(filePath)
                        else:
                            raise QgsProcessingException(self.tr("Input layer '{}' has unsupported format.".format(param.name())))
                self.layers[param.name()] = files

        return commands

    def processAlgorithm(self, parameters, context, feedback):
        exportCommands = self.convertLayers(parameters, context, feedback)

        arguments = []
        for param in self.parameterDefinitions():
            if not param.name() in parameters or parameters[param.name()] is None:
                continue

            if param.isDestination():
                continue

            if isinstance(param, (QgsProcessingParameterRasterLayer, QgsProcessingParameterFeatureSource)):
                arguments.append("-{} '{}'".format(param.name(), self.layers[param.name()]))
            elif isinstance(param, QgsProcessingParameterMultipleLayers):
                arguments.append("-{} '{}'".format(param.name(), ";".join(self.layers[param.name()])))
            elif isinstance(param, QgsProcessingParameterMatrix):
                cols = len(param.headers())
                tableFile = QgsProcessingUtils.generateTempFilename("table.txt")
                with open(tableFile, "w", encoding="utf-8") as f:
                    f.write("{}\n".format("\t".join(param.headers())))

                    values = self.parameterAsMatrix(parameters, param.name(), context)
                    for i in range(0, len(values), cols):
                        f.write("{}\n".format("/t".join(values[i:i + cols])))

                arguments.append("-{} '{}'".format(param.name(), tableFile))
            elif isinstance(param, QgsProcessingParameterExtent):
                extent = self.parameterAsExtent(parameters, param.name(), context)

                #FIXME: is adjusting needed?
                values = [extent.xMinimum(), extent.xMaximum(), extent.yMinimum(), extent.yMaximum()]
                for k, v in zip(self.extentParams, values):
                    arguments.append("-{} {}".format(k, v))
            elif isinstance(param, QgsProcessingParameterRange):
                values = self.parameterAsRange(parameters, param.name(), context)
                arguments.append("-{}_MIN {}".format(param.name(), values[0]))
                arguments.append("-{}_MAX {}".format(param.name(), values[1]))
            elif isinstance(param, QgsProcessingParameterNumber):
                value = None
                if param.dataType() == QgsProcessingParameterNumber.Integer:
                    value = self.parameterAsInt(parameters, param.name(), context)
                else:
                    value = self.parameterAsDouble(parameters, param.name(), context)
                arguments.append("-{} {}".format(param.name(), value))
            elif isinstance(param, QgsProcessingParameterBoolean):
                if self.parameterAsBool(parameters, param.name(), context):
                    arguments.append("-{} true".format(param.name()))
                else:
                    arguments.append("-{} false".format(param.name()))
            elif isinstance(param, QgsProcessingParameterEnum):
                arguments.append("-{} {}".format(param.name(), self.parameterAsEnum(parameters, param.name(), context)))
            else:
                arguments.append("-{} '{}'".format(param.name(), self.parameterAsString(parameters, param.name(), context)))

        for out in self.destinationParameterDefinitions():
            if isinstance(out, (QgsProcessingParameterRasterDestination, QgsProcessingParameterVectorDestination)):
                arguments.append("-{} '{}'".format(out.name(), self.parameterAsOutputLayer(parameters, out.name(), context)))
            elif isinstance(out, (QgsProcessingParameterFileDestination, QgsProcessingParameterFolderDestination)):
                arguments.append("-{} '{}'".format(out.name(), self.parameterAsFileOutput(parameters, out.name(), context)))
            else:
                arguments.append("-{} '{}'".format(param.name(), self.parameterAsString(parameters, out.name(), context)))

        commands = []
        commands.extend(exportCommands)
        commands.append("{} '{}' {}".format(self.groupId(), self.name(), " ".join(arguments)))

        sagaUtils.execute(commands, feedback)

        results = {}
        for output in self.outputDefinitions():
            outputName = output.name()
            if outputName in parameters:
                results[outputName] = parameters[outputName]

        return results
