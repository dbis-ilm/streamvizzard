from kafka3 import KafkaProducer
from typing import Optional, Dict, List

from spe.pipeline.operators.sink import Sink
from spe.runtime.compiler.codegeneration.frameworks.pyFlink.pyFlinkUtils import PyFlinkJARs
from spe.runtime.compiler.definitions.compileDefinitions import CompileFramework, CompileLanguage, CompileComputeMode, \
    CompileParallelism
from spe.runtime.compiler.definitions.compileOpFunction import CodeTemplateCOF
from spe.runtime.compiler.definitions.compileOpSpecs import CompileOpSpecs
from spe.common.tuple import Tuple


class KafkaSink(Sink):
    def __init__(self, opID: int):
        super().__init__(opID, 1)

        self.broker = ""
        self.port = 0
        self.topic = ""
        self.encoding = "utf-8"
        self.maxRequestSize = 1048588

        self._producer: Optional[KafkaProducer] = None

    def setData(self, data: Dict):
        changed = ((self.port != data["port"]) or (self.broker != data["broker"])
                   or (self.topic != data["topic"]) or (self.maxRequestSize != data["maxRequestSize"]))

        self.port = data["port"]
        self.broker = data["broker"]
        self.topic = data["topic"]
        self.maxRequestSize = data["maxRequestSize"]

        self.encoding = data["encoding"]

        if changed:
            self._closeProducer()

    def getData(self) -> dict:
        return {"port": self.port, "broker": self.broker, "topic": self.topic,
                "encoding": self.encoding, "maxRequestSize": self.maxRequestSize}

    def onRuntimeDestroy(self):
        super(KafkaSink, self).onRuntimeDestroy()

        self._closeProducer()

    def _closeProducer(self):
        if self._producer is not None:
            self._producer.close()
            self._producer = None

    def _verifyProducer(self):
        if self._producer is not None:
            return

        try:
            self._producer = KafkaProducer(bootstrap_servers=f"{self.broker}:{self.port}", max_request_size=self.maxRequestSize)
        except Exception:
            self.onExecutionError()

    def _execute(self, tupleIn: Tuple) -> Optional[Tuple]:
        self._verifyProducer()

        if self._producer is None:
            return None  # Error opening producer

        # Kafka expects byte data
        dataToSend = tupleIn.data[0].encode(self.encoding)

        try:
            self._producer.send(self.topic, value=dataToSend)

            self._producer.flush()

            return self.createSinkTuple()
        except Exception:
            return self.createErrorTuple()

    # -------------------------- Compilation -------------------------

    def getCompileSpecs(self) -> List[CompileOpSpecs]:
        def getPyFlinkCode(compileConfig):
            from spe.runtime.compiler.codegeneration.frameworks.pyFlink.pyFlinkCodeTemplate import PyFlinkCodeTemplate

            pyFlinkCode = PyFlinkCodeTemplate({
                PyFlinkCodeTemplate.Section.IMPORTS: """
            from pyflink.datastream.connectors.kafka import KafkaSink, KafkaRecordSerializationSchema
            from pyflink.common.serialization import SimpleStringSchema""",
                PyFlinkCodeTemplate.Section.FUNCTION_DECLARATION: f"""
            ks_{self.getUniqueName()} = KafkaSink.builder() \\
                .set_bootstrap_servers("{self.broker}:{self.port}") \\
                .set_record_serializer(KafkaRecordSerializationSchema.builder()
                                       .set_topic("{self.topic}")
                                       .set_value_serialization_schema(SimpleStringSchema("{self.encoding}"))
                                       .build()) \\
                .build()
            """,
                PyFlinkCodeTemplate.Section.ASSIGNMENTS: f"""
            $inDS.add_sink(ks_{self.getUniqueName()})"""},
                jarDependencies=[PyFlinkJARs.FLINK_KAFKA_CONNECTOR])

            return pyFlinkCode

        return [CompileOpSpecs.getSVDefault(),
                CompileOpSpecs([CompileFramework.PYFLINK],
                               [CompileLanguage.PYTHON],
                               [CompileComputeMode.CPU],
                               CompileParallelism.all(),
                               compileFunction=CodeTemplateCOF(CodeTemplateCOF.Type.SINK, getPyFlinkCode))]
