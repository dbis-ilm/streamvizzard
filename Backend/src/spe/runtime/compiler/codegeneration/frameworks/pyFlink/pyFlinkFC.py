from __future__ import annotations

import logging
import os
import re
import textwrap
import traceback
from collections import defaultdict
from string import Template
from typing import TYPE_CHECKING, Optional, Dict, List, Set

import autopep8

from spe.common.dataType import DataType
from spe.pipeline.operators.base.operators.transform.parseJSON import ParseJSON
from spe.pipeline.operators.base.operators.transform.serializeJSON import SerializeJSON
from spe.runtime.compiler.codegeneration.frameworks.common.pythonUtils import extractDependencyList
from spe.runtime.compiler.compilerRes import CompilerRes
from spe.runtime.compiler.codegeneration.frameworks.frameworkCompiler import FrameworkCompiler
from spe.runtime.compiler.codegeneration.frameworks.pyFlink.pyFlinkCodeTemplate import PyFlinkCodeTemplate
from spe.runtime.compiler.codegeneration.frameworks.pyFlink.pyFlinkStatics import pyFlinkSerializationModule, \
    pyFlinkCustomJSONDeserializerDict, pyFlinkReorderEventsOpDef, \
    pyFlinkReorderEventsOpAssign, pyFlinkJoinOpDef, pyFlinkJoinOpAssign, pyFlinkOrderedJoinOpDef, \
    pyFlinkOrderedJoinOpAssign, pyFlinkEventTimeAssignerDef, pyFlinkEventTimeAssigner
from spe.runtime.compiler.codegeneration.frameworks.pyFlink.pyFlinkUtils import PyFlinkStruct, PyFlinkJARs, \
    getPyFlinkTypeFor, PyFlinkTags
from spe.runtime.compiler.codegeneration.nativeCodeExtractor import NativeCodeExtractor, ModuleExtractor, ClassExtractor
from spe.runtime.compiler.definitions.compileDefinitions import CompileFrameworkConnector, CompileLanguage
from spe.runtime.compiler.definitions.compileOpFunction import CodeTemplateCOF, CompileOpFunction, InferExecutionCodeCOF
from spe.runtime.compiler.opCompileData import OpCompileData
from spe.runtime.compiler.placement.knowledgeProvider.executionStatsKP import ExecutionStatsKP
from spe.runtime.compiler.placement.knowledgeProvider.opKnowledgeProvider import OpKnowledgeType
from streamVizzard import StreamVizzard
from spe.pipeline.connection import Connection
from spe.runtime.compiler.opCompileConfig import OpCompileConfig
from utils.utils import printWarning

if TYPE_CHECKING:
    from spe.pipeline.operators.operator import Operator
    from spe.runtime.compiler.definitions.compileFrameworkSpecs import CompileFrameworkSpecs
    from spe.pipeline.socket import Socket
    from spe.runtime.compiler.codegeneration.codeGenerator import CodeGenerator

# Single value tuples are transmitted as literal values. Tuples with multiple elements are transmitted as tuples.
# During joins, the input data from both sides are joined into one result tuple.
# If an operator has more than one output, the full data is transmitted to all connected ops and accessed with socketID.


class PyFlinkFC(FrameworkCompiler):
    def __init__(self, framework: CompileFrameworkSpecs, clusterID: int, generator: CodeGenerator):
        super().__init__(framework, clusterID, generator)

        self._imports: List[str] = list()
        self._opFunctions: List[tuple[int, str]] = list()
        self._opAssignments: List[tuple[int, str]] = list()

        # Specifies the input ds [opID, name] for each operator, None for sources
        self._inputDsMapping: Dict[int, Optional[PyFlinkFC.DSMapping]] = dict()
        self._opDependenciesMapping: Dict[int, List[int]] = dict()  # key op depends on value ops

        self._jarDependencies: Set[PyFlinkJARs] = set()
        self._helperFuncs: Dict[str, PyFlinkStruct] = dict()

    def generateCode(self) -> CompilerRes:
        # Future Work: Bundle Time/Size, Network Buffer (also per operator) Timeouts could be optimized based on throughput and data sizes from catalog

        template = Template(textwrap.dedent("""
        \"""
        $disclaimer
        \"""
        
        from __future__ import annotations
        $imports

        # Create the execution environment
        
        config = Configuration()
        config.set_integer("python.fn-execution.bundle.time", 1000)
        
        env = StreamExecutionEnvironment.get_execution_environment(config)
        env.set_runtime_mode(RuntimeExecutionMode.STREAMING)
        $envCfg
        
        # ------------------------ Utils -------------------------
        $helper
        # ---------------------- Operators -----------------------
        
        
        $opFunctions
        
        
        # ---------------- Pipeline Construction -----------------
        
        # autopep8: off
        $pipeline
        # autopep8: on
        
        # Execute the pipeline
        
        env.execute()
        """))

        # Generate operator code, joins and config

        if not self._generateOperatorCode():
            return CompilerRes("Failed to generate PyFlink code!")

        # Sort code and assigns to have a valid order

        self._sortOperatorCode()

        serRes = self._handleDataSerialization()

        if serRes.hasError():
            return serRes

        # Setup streaming environment

        if self._requiresEventTime():
            envCfg = "env.set_stream_time_characteristic(TimeCharacteristic.EventTime)"
        else:
            envCfg = "env.set_stream_time_characteristic(TimeCharacteristic.ProcessingTime)"

        # Collect imports

        opImports = [imp for imp in self._imports]
        helperImports = [hf.imports for hf in self._helperFuncs.values() if hf.imports is not None]
        globalImports = ["from pyflink.datastream import StreamExecutionEnvironment",
                         "from pyflink.datastream import RuntimeExecutionMode, TimeCharacteristic",
                         "from pyflink.common import Types",
                         "from pyflink.common import Configuration"]

        # Collect code sections

        opFunctions = "\n\n\n".join([func[1].strip() for func in self._opFunctions])

        pipeline = "\n".join([a[1].strip() for a in self._opAssignments])

        helperCode = ""

        for helper in self._helperFuncs.values():
            helperCode += "\n\n" + helper.funcCode.strip() + "\n"

        imports = self._getUniqueImports(opImports + helperImports + globalImports)

        # Generate complete project code

        code = template.substitute(disclaimer=StreamVizzard.getConfig().COMPILER_CODE_GEN_DISCLAIMER,
                                   imports="\n".join(imports).strip(),
                                   envCfg=envCfg,
                                   helper=helperCode,
                                   opFunctions=opFunctions.strip(),
                                   pipeline=pipeline.strip()).strip()

        code = autopep8.fix_code(code)
        code = re.sub(r'^[ \t]*#\s*autopep8:\s*(on|off)[ \t]*\n?', '', code, flags=re.MULTILINE)  # Remove autopep annotations

        # Write actual code file

        outputFolder = os.path.join(self.generator.getOutputPath(), "PyFlink_" + str(self.clusterID))
        os.makedirs(outputFolder, exist_ok=True)

        try:
            with open(os.path.join(outputFolder, "pipeline.py"), "w") as f:
                f.write(code)
                f.write("\n")
        except Exception:
            logging.log(logging.ERROR, traceback.format_exc())

            return CompilerRes("Failed to save pipeline file!")

        # Print dependency instructions

        pythonDeps = sorted(extractDependencyList(imports))

        dependencyText = "Required Python packages for execution:\n"

        for dep in pythonDeps:
            dependencyText += dep + "\n"

        if len(self._jarDependencies) > 0:
            dependencyText += "\nRequired JARs for execution:\n"

            for jar in self._jarDependencies:
                dependencyText += f"{jar.value[0]} ({jar.value[1]})\n"

        dependencyText += "\nUsage: jobmanager ./bin/flink run -py [pipelineFile] --jarfile [jarFile]\n"

        try:
            with open(os.path.join(outputFolder, "dependencies.txt"), "w") as f:
                f.write(dependencyText)
        except Exception:
            logging.log(logging.ERROR, traceback.format_exc())

            return CompilerRes("Failed to save dependency file!")

        return CompilerRes.ok()

    def mergeWith(self, otherCp: PyFlinkFC) -> bool:
        for op in otherCp.opNodes:
            self.registerOperator(op)

        return True

    def registerConnector(self, cc: OpCompileConfig.ClusterConnectionConfig, con: Connection, socket: Socket) -> CompilerRes:
        if cc.conType == CompileFrameworkConnector.APACHE_KAFKA:
            return self._generateKafkaConnector(cc, socket, CompileLanguage.PYTHON)

        return CompilerRes(f"No PyFlink connector implementation found for {cc.conType}")

    # ---------------------------------------------- Operator Generation -----------------------------------------------

    def _generateOperatorCode(self) -> bool:
        if not self._generateJoins():
            return False

        for op in self.opNodes:
            cf = op.specsCatalog.getCompileFunction(op.compileConfig)

            if cf is None:
                op.operator.onExecutionError("No compile function found!")

                return False

            if isinstance(cf, CodeTemplateCOF):
                codeTemplate = cf.templateGetter(op.compileConfig)

                assert isinstance(codeTemplate, PyFlinkCodeTemplate)

                if not self._generateOpFromTemplate(op, cf.functionType, codeTemplate):
                    return False
            elif isinstance(cf, InferExecutionCodeCOF):
                extr = cf.infer(op.operator, op.compileConfig)

                if extr is None:
                    return False

                # Fix return values of our inferred function body
                # -> if only one output exists and op is not a filter (which returns bool) add [0] access

                if cf.functionType == CompileOpFunction.Type.FILTER:
                    if len(op.operator.outputs) > 1:
                        op.operator.onExecutionError("Filter with more than one output are not supported!")

                        return False
                elif len(op.operator.outputs) == 1:
                    extr.disassemblyReturnTuple()

                cf.performInputRenaming(extr)

                res = extr.extract(True)

                if res is None:
                    return False

                for classExtr in res.classExtracts:
                    if not self._handleCustomClassExtracts(classExtr):
                        op.operator.onExecutionError(f"Couldn't extract custom class {classExtr.moduleName} due to internal SV references and no override available!")

                        return False

                codeTemplate = PyFlinkCodeTemplate({PyFlinkCodeTemplate.Section.IMPORTS: res.imports,
                                                    PyFlinkCodeTemplate.Section.FUNCTION_CONTENT: res.code})

                if not self._generateOpFromTemplate(op, cf.functionType, codeTemplate):
                    return False

        return True

    def _generateJoins(self) -> bool:
        # Tracks input DS mapping, op dependencies and generates required joins

        for op in self.opNodes:
            inCount = len(op.operator.inputs)

            # Register "NONE" (env) for operators without input (sources)
            if inCount == 0:
                self._inputDsMapping[op.operator.id] = None

            # Register the connected IN op as inputDS for our op [only for 1-input ops]
            elif inCount == 1:
                firstSock = op.operator.inputs[0]

                if firstSock.hasConnections():
                    inputOp = firstSock.getConnections()[0].output.op

                    self._inputDsMapping[op.operator.id] = PyFlinkFC.DSMapping(inputOp.id, inputOp.getUniqueName())
                    self._opDependenciesMapping[op.operator.id] = [inputOp.id]
                else:  # We have an input socket but no connected op [disconnected op]
                    self._inputDsMapping[op.operator.id] = None

            elif inCount > 2:  # Not supported
                return False

            if inCount <= 1:
                continue

            # Generate joins for all operators with more than one input

            newOpID = self._generateNewOpID(True)
            newOpName = f"Join_{newOpID}"

            # Find both streams connected to our op

            stream1Op = None
            stream2Op = None

            dependencies: List[int] = []

            for i in op.operator.inputs:
                if i.hasConnections():
                    otherOp = i.getConnections()[0].output.op

                    if stream1Op is None:
                        stream1Op = otherOp
                    else:
                        stream2Op = otherOp

                    dependencies.append(otherOp.id)

            self._opDependenciesMapping[newOpID] = dependencies

            # Register this new join as an input ds for the actual operator

            self._inputDsMapping[op.operator.id] = PyFlinkFC.DSMapping(newOpID, newOpName)
            self._opDependenciesMapping[op.operator.id] = [newOpID]

            # Retrieve type hints

            outTypeStream1 = self._createDataTypeHint(next((elm for elm in self.opNodes if elm.operator.id == stream1Op.id)))
            outTypeStream2 = self._createDataTypeHint(next((elm for elm in self.opNodes if elm.operator.id == stream2Op.id)))

            typeHint = None

            if outTypeStream1 is not None and outTypeStream2 is not None:
                typeHint = f"Types.TUPLE([{outTypeStream1}, {outTypeStream2}])"

            # Generate the actual join operator

            stream1 = stream1Op.getUniqueName()
            stream2 = stream2Op.getUniqueName()

            # Generate a helper function for combining the both streams.
            # Distinguish between order-restoring and normal joins

            parallelism = op.compileConfig.parallelismCount

            if op.reorderTuples():
                joinOpDef = pyFlinkOrderedJoinOpDef
                joinOpAssign = pyFlinkOrderedJoinOpAssign

                joinProcessFuncAssign = joinOpAssign.substitute(typeHint=typeHint, parallelism=parallelism,
                                                                keyFunc=self._getArbitraryKeyByFunc(parallelism))
            else:
                joinOpDef = pyFlinkJoinOpDef
                joinOpAssign = pyFlinkJoinOpAssign

                joinProcessFuncAssign = joinOpAssign.substitute(typeHint=typeHint, parallelism=parallelism)

            self._opAssignments.append((newOpID, f"{newOpName} = {stream1}.connect({stream2}){joinProcessFuncAssign}"))
            self._registerHelperStruct(joinOpDef)

        return True

    def _generateOpFromTemplate(self, opData: OpCompileData, funcType: CompileOpFunction.Type, codeTemplate: PyFlinkCodeTemplate) -> bool:
        op = opData.operator

        # Handle JAR dependencies

        for dp in codeTemplate.jarDependencies:
            self._jarDependencies.add(dp)

        # Handle struct dependencies

        for sd in codeTemplate.structDependencies:
            self._registerHelperStruct(sd)

        # Handle imports

        imports = codeTemplate.get(PyFlinkCodeTemplate.Section.IMPORTS)

        if imports is not None:
            self._imports.append(imports.substitute())

        # Handle operator function

        self._generateOpFunction(op, funcType, codeTemplate)

        return self._generateOpAssignment(opData, funcType, codeTemplate)

    def _generateOpFunction(self, op: Operator, funcType: CompileOpFunction.Type, codeTemplate: PyFlinkCodeTemplate):
        funcDeclaration = codeTemplate.get(PyFlinkCodeTemplate.Section.FUNCTION_DECLARATION)
        funcContent = codeTemplate.get(PyFlinkCodeTemplate.Section.FUNCTION_CONTENT)

        funcCode: Optional[str] = None

        if funcDeclaration is not None:
            funcCode = funcDeclaration.safe_substitute(input="$inTuple").strip()
        elif funcContent is not None:
            funcCode = f"def {funcType.value}_{op.getUniqueName()}(inTuple):\n"

            # Make sure all of our content has the correct indentation
            contentCode = funcContent.safe_substitute(input="$inTuple").strip()
            indentedContent = "\n".join("    " + line for line in contentCode.splitlines())

            funcCode += indentedContent

        if funcCode is None:
            return

        # --- Handle input tuple cardinality ---

        # If only one input exists, we replace [0] array access with direct value access

        if len(op.inputs) == 1:
            funcCode = funcCode.replace("$inTuple[0]", "$inTuple")

        # Add tuple access if input operators have more than one output (need to access appropriate part of result)

        for inCon in op.getConnections(True, False):
            inOp = inCon.output.op

            if len(inOp.outputs) <= 1:
                continue

            inAccess = f"$inTuple" if len(op.inputs) == 1 else f"$inTuple[{inCon.input.id}]"

            funcCode = funcCode.replace(inAccess, f"{inAccess}[{inCon.output.id}]")

        funcCode = funcCode.replace("$inTuple", "inTuple")

        self._opFunctions.append((op.id, funcCode))

    def _generateOpAssignment(self, opData: OpCompileData, funcType: CompileOpFunction.Type, codeTemplate: PyFlinkCodeTemplate) -> bool:
        op = opData.operator
        cfg = opData.compileConfig

        # Get inputDS for this op

        inputDS = self._inputDsMapping.get(op.id, None)
        inDS = inputDS.dsName if inputDS is not None else "env"

        # Inject reorder operator if out-of-order processing is detected and desired by user [joins handled separately]

        if opData.reorderTuples() and len(op.inputs) == 1:
            self._registerHelperStruct(pyFlinkReorderEventsOpDef)

            keyFunc = self._getArbitraryKeyByFunc(cfg.parallelismCount)

            # Reorder operator is added before our actual operator and need to consider input data types

            inTypeHint = PyFlinkFC._createDataTypeHint(opData, False)
            inDS = inDS + pyFlinkReorderEventsOpAssign.substitute(typeHint=inTypeHint, keyFunc=keyFunc, parallelism=cfg.parallelismCount)

        # Handle assignment(s) to pipeline

        typeHint = PyFlinkFC._createDataTypeHint(opData)

        def injectAssignmentParams(assignmentCode: str):
            # Injects additional information such as parallelism and typehint to the assignment code

            # Extracts assignment function such as map, filter, from_source, window, ...

            assignmentFunc = NativeCodeExtractor.extractFunctionName(assignmentCode)

            if assignmentFunc is None:
                return False

            # Inject type hints

            assignmentCode = self._addAssignmentTypeHint(assignmentFunc, assignmentCode, typeHint)

            # Handle sources

            if self._isSourceAssignment(assignmentFunc):
                # Add custom watermark strategy for sources

                self._imports.append("from pyflink.common import WatermarkStrategy")

                # Currently, we assume that there is no out-of-order arrival of source data (e.g. Kafka)
                # Otherwise, we might need to switch to .for_bounded_out_of_orderness

                ws = "WatermarkStrategy.for_monotonous_timestamps()"

                # Consider idleness for unbounded sources to avoid watermark progression getting stuck on joined sources

                if codeTemplate.hasTag(PyFlinkTags.SOURCE_UNBOUNDED):
                    self._imports.append("from pyflink.common import Duration")

                    ws += ".with_idleness(Duration.of_seconds(10))"

                # Insert custom TimeStamp assigner if pipeline requires event times [currently only during reorder]

                if self._requiresEventTime():
                    self._registerHelperStruct(pyFlinkEventTimeAssignerDef)

                    ws += f".with_timestamp_assigner({pyFlinkEventTimeAssigner}())"

                # Need to specify parallelism on the source first, since .assign_timestamps creates a new stream

                assignmentCode = assignmentCode + f".set_parallelism({cfg.parallelismCount})"

                # .assign_timestamps overrides the already defined strategy of the sources
                # If a custom TimestampAssigner is defined, an artificial python udf operator with parallelism=1 is inserted
                # to extract the timestamps. However, we can't directly put the TimestampAssigner in the watermark attribute
                # of the sources, since they only respect the (Java) watermark strategy.

                assignmentCode += f".assign_timestamps_and_watermarks({ws})"

            # Handle parallelism

            if self._canAssignParallelism(assignmentFunc):
                assignmentCode = assignmentCode + f".set_parallelism({cfg.parallelismCount})"

            return assignmentCode

        assignments = codeTemplate.get(PyFlinkCodeTemplate.Section.ASSIGNMENTS)

        combinedAssignment = None

        if assignments is None:
            assignmentCall = self._getAssignmentCall(funcType)

            if assignmentCall is None:
                return False

            combinedAssignment = f"{inDS}.{assignmentCall}({funcType.value}_{op.getUniqueName()})"
            combinedAssignment = injectAssignmentParams(combinedAssignment)
        else:
            if not isinstance(assignments, list):
                assignments = [assignments]

            for assignment in assignments:
                inputStream = inDS if combinedAssignment is None else combinedAssignment  # Chain all previous calls
                combinedAssignment = injectAssignmentParams(assignment.safe_substitute(inDS=inputStream).strip())

        self._opAssignments.append((op.id, f"{op.getUniqueName()} = " + combinedAssignment))

        return True

    @staticmethod
    def _getAssignmentCall(funcType: CompileOpFunction.Type) -> Optional[str]:
        assignmentCall = None

        if funcType == CompileOpFunction.Type.MAP:
            assignmentCall = "map"
        elif funcType == CompileOpFunction.Type.FILTER:
            assignmentCall = "filter"

        return assignmentCall

    @staticmethod
    def _addAssignmentTypeHint(funcName: str, assignmentCode: str, typeHint: str) -> Optional[str]:
        opNames = ["map", "process", "flat_map", "reduce", "aggregate", "apply"]

        if PyFlinkFC._isSourceAssignment(funcName):
            typeHintAttribute = "type_info"
        elif funcName in opNames:
            typeHintAttribute = "output_type"
        else:
            return assignmentCode

        # Get type information if required

        if typeHint is None:
            return assignmentCode

        return NativeCodeExtractor.addNamedFunctionAttribute(assignmentCode, typeHintAttribute, typeHint)

    @staticmethod
    def _isSourceAssignment(funcName: str):
        return funcName in ["from_source", "add_source"]

    @staticmethod
    def _createDataTypeHint(opData: OpCompileData, output: bool = True) -> Optional[str]:
        sockCount = len(opData.operator.outputs) if output else len(opData.operator.inputs)

        if sockCount == 0:
            return None

        exStats: ExecutionStatsKP = opData.getKnowledgeProvider(OpKnowledgeType.EXECUTION_STATS)
        stats = exStats.getStats()

        if stats is None:
            return None

        def getTypeForSocket(sockID: int) -> Optional[str]:
            socketData = stats.outDataTypes.getSocketData(sockID) if output else stats.inDataTypes.getSocketData(sockID)

            # Only enter a type hint if only one data type is processed.
            # Some type hints (DOUBLE, ...) do not support None values, in this case we do not provide a type hint at all.
            socketType = socketData.getUniformType()

            return getPyFlinkTypeFor(socketType)

        if sockCount == 1:
            return getTypeForSocket(0)
        else:
            socketTypes = []

            for i in range(sockCount):
                t = getTypeForSocket(i)

                if t is None:  # Missing subTypes not supported -> replace with default
                    t = "Types.PICKLED_BYTE_ARRAY()"

                socketTypes.append(t)

            return f"Types.TUPLE([{', '.join(socketTypes)}])"

    @staticmethod
    def _canAssignParallelism(funcName: str) -> bool:
        notAllowedOps = ["key_by", "window_all", "window"]

        return funcName not in notAllowedOps

    def _requiresEventTime(self):
        # Checks, if the pipeline requires the usage of EventTime

        # Currently, the pipeline only requires EventTime, if any operator enforces a reorder of the data.

        for opData in self.opNodes:
            if opData.reorderTuples():
                return True

        return False

    @staticmethod
    def _getArbitraryKeyByFunc(parallelism: int):
        # For para=1 we can use constant key for faster partitioning to assign all values to same (single) partition.
        # For higher parallelism we choose hashed keys based on data and rely on automated distribution across nodes.

        return "lambda x: 1" if parallelism == 1 else "lambda x: hash(str(x))"

    # ----------------------------------------------------- Utils ------------------------------------------------------

    def _handleCustomClassExtracts(self, extract: ClassExtractor.Result) -> bool:
        if extract.internalImports:
            printWarning(f"Couldn't extract custom class {extract.moduleName} due to internal SV references and no override available!")

            return False  # Note: We may supply overrides for custom classes here!

        self._registerHelperStruct(PyFlinkStruct(extract.moduleName, extract.classCode, extract.imports))

        return True

    def _handleDataSerialization(self) -> CompilerRes:
        # Manages serialization between frameworks and into/out of the pipeline [not serialization between ops]
        # Checks occurrence of ParseJSON and SerializeJSON which is used for inter-pipeline communication!
        # We expect customTypes to implement the fromJSON [static] and toJSON method!

        # Detect all involved (nested) dataTypes in the pipeline

        typeLookup: Dict[str, DataType] = dict()
        needsSerialization = False

        def extractTypes(oData: OpCompileData, inTypes: bool, outTypes: bool):
            exStats: ExecutionStatsKP = oData.getKnowledgeProvider(OpKnowledgeType.EXECUTION_STATS)
            stats = exStats.getStats()

            if stats is None:
                return

            if inTypes:
                for inID in range(len(operator.inputs)):
                    sockData = stats.inDataTypes.getSocketData(inID)

                    dt = sockData.getUniformType()

                    if dt is not None:
                        for nt in dt.getNestedTypes():
                            typeLookup[nt.typeName] = nt

            if outTypes:
                for outID in range(len(operator.outputs)):
                    sockData = stats.outDataTypes.getSocketData(outID)

                    dt = sockData.getUniformType()

                    if dt is not None:
                        for nt in dt.getNestedTypes():
                            typeLookup[nt.typeName] = nt

        for opData in self.opNodes:
            operator = opData.operator

            if isinstance(operator, ParseJSON):
                # Check out dataTypes which we parse into
                extractTypes(opData, False, True)
                needsSerialization = True

            if isinstance(operator, SerializeJSON):
                # Check in dataTypes that need to be parsed
                extractTypes(opData, True, False)
                needsSerialization = True

        if not needsSerialization:
            return CompilerRes.ok()

        # Export all custom non-system types!

        # We differentiate between dataTypes that are used inside the code [NativeCodeExtractor]
        # and those used during serialization [Here]. Export custom types from serialization here as well as backup.

        exportableCustomTypes = [dt for dt in typeLookup.values() if not dt.definition.systemType]

        customDeserializer = ""

        for ct in exportableCustomTypes:
            # Extract and export type

            typeName = ct.definition.getValueTypeName()

            customTypeExtract = ClassExtractor(typeName, ct.definition.getValueType()).extract(True)

            if customTypeExtract is not None:
                if not self._handleCustomClassExtracts(customTypeExtract):
                    return CompilerRes(f"Couldn't extract custom class {customTypeExtract.moduleName} due to internal SV references and no override available!")
            else:
                return CompilerRes(f"Couldn't extract custom dataType {typeName}!")

            # Generate custom serialization instructions

            if len(customDeserializer) != 0:
                customDeserializer += "\n"

            customDeserializer += f"{pyFlinkCustomJSONDeserializerDict}['{typeName}'] = {typeName}.fromJSON"

        # Extract custom serializer functions

        serializationExtract = ModuleExtractor(pyFlinkSerializationModule).extract(False)

        serializationCode = serializationExtract.moduleCode + "\n\n" + customDeserializer

        # Register last [for ordering - insertion-based]
        self._registerHelperStruct(PyFlinkStruct("serialization", serializationCode, serializationExtract.imports))

        return CompilerRes.ok()

    def _sortOperatorCode(self):
        # Ensure an order of assignments and op function definition so that every operator is defined when used

        graph: dict[int, list[int]] = defaultdict(list)

        for key, values in self._opDependenciesMapping.items():
            for value in values:
                graph[value].append(key)

        visited = set()
        tempMark = set()
        sortedOrder = []

        def dfs(node):
            if node in tempMark:
                raise ValueError("Cycle in sorting operators! " + str(node))

            if node not in visited:
                tempMark.add(node)

                for neighbour in graph[node]:
                    dfs(neighbour)

                tempMark.remove(node)
                visited.add(node)
                sortedOrder.append(node)

        allOps = set(self._opDependenciesMapping.keys()).union(*self._opDependenciesMapping.values())

        for op in allOps:
            if op not in visited:
                dfs(op)

        finalOrder = sortedOrder[::-1]  # Reverse
        orderIdx = {opID: index for index, opID in enumerate(finalOrder)}

        # Here we support 0 as fallback index/order for disconnected operators

        self._opFunctions = sorted(self._opFunctions, key=lambda x: orderIdx.get(x[0], 0))
        self._opAssignments = sorted(self._opAssignments, key=lambda x: orderIdx.get(x[0], 0))

    def _registerHelperStruct(self, function: PyFlinkStruct):
        """ Helper structs are added only once by unique name """

        if function.name not in self._helperFuncs:
            self._helperFuncs[function.name] = function

    @staticmethod
    def _getUniqueImports(importList: List[str]) -> List[str]:
        imports = "\n".join([imp.strip() for imp in importList])

        # Remove duplicates

        lines = imports.strip().split("\n")

        uniqueImports: Set[str] = set()

        for line in lines:
            uniqueImports.add(line.strip())

        sortedList = sorted(list(uniqueImports), key=lambda x: len(x))

        return sortedList

    class DSMapping:
        def __init__(self, opID: int, dsName: str):
            self.opID = opID
            self.dsName = dsName
