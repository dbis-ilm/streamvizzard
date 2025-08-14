from kafka3 import KafkaConsumer
from typing import Optional, Dict, List

from spe.pipeline.operators.source import Source
from spe.runtime.compiler.codegeneration.frameworks.pyFlink.pyFlinkUtils import PyFlinkJARs, PyFlinkTags
from spe.runtime.compiler.definitions.compileDefinitions import CompileFramework, CompileComputeMode, CompileLanguage, \
    CompileParallelism
from spe.runtime.compiler.definitions.compileOpFunction import CodeTemplateCOF
from spe.runtime.compiler.definitions.compileOpSpecs import CompileOpSpecs


class KafkaSource(Source):
    def __init__(self, opID: int):
        super().__init__(opID, 0, 1)

        self.broker = ""
        self.port = 0
        self.topic = ""
        self.groupID = ""
        self.offset = ""
        self.encoding = "utf-8"

        self._earliestOffset = False
        self._consumer: Optional[KafkaConsumer] = None

    def setData(self, data: Dict):
        changed = ((self.port != data["port"]) or
                   (self.broker != data["broker"]) or
                   (self.topic != data["topic"]) or
                   (self.groupID != data["groupID"]))

        self.port = data["port"]
        self.broker = data["broker"]
        self.topic = data["topic"]
        self.groupID = data["groupID"]
        self.offset = data["offset"]

        self.encoding = data["encoding"]

        self._earliestOffset = self.offset == "earliest"  # Else its latest

        if changed:
            self._closeConsumer()

    def getData(self) -> dict:
        return {"port": self.port, "broker": self.broker, "topic": self.topic,
                "groupID": self.groupID, "offset": self.offset, "encoding": self.encoding}

    def onRuntimeDestroy(self):
        super(KafkaSource, self).onRuntimeDestroy()

        self._closeConsumer()

    def _closeConsumer(self):
        if self._consumer is not None:
            self._consumer.close()
            self._consumer = None

    def _verifyConsumer(self):
        if self._consumer is not None:
            return

        offset = "earliest" if self._earliestOffset else "latest"

        try:
            self._consumer = KafkaConsumer(self.topic,
                                           bootstrap_servers=f"{self.broker}:{self.port}",
                                           group_id=self.groupID,
                                           auto_offset_reset=offset)
        except Exception:
            self.onExecutionError()

    def _runSource(self):
        while self.isRunning():
            self._verifyConsumer()

            if self._consumer is None:  # Time for reconnecting
                continue

            try:
                for message in self._consumer:
                    self._produce((message.value.decode(self.encoding),))  # Kafka sends byte data
            except Exception:
                if self.isRunning():
                    self.onExecutionError()

        self._closeConsumer()

    # -------------------------- Compilation -------------------------

    def getCompileSpecs(self) -> List[CompileOpSpecs]:
        def getPyFlinkCode(compileConfig):
            from spe.runtime.compiler.codegeneration.frameworks.pyFlink.pyFlinkCodeTemplate import PyFlinkCodeTemplate

            pyFlinkCode = PyFlinkCodeTemplate({
                PyFlinkCodeTemplate.Section.IMPORTS: """
            from pyflink.common.serialization import SimpleStringSchema
            from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer
            from pyflink.common import WatermarkStrategy""",
                PyFlinkCodeTemplate.Section.FUNCTION_DECLARATION: f"""
            kafkaSource_{self.getUniqueName()} = KafkaSource.builder() \\
                .set_bootstrap_servers("{self.broker}:{self.port}") \\
                .set_group_id("{self.groupID}") \\
                .set_topics("{self.topic}") \\
                .set_starting_offsets({"KafkaOffsetsInitializer.earliest()" if self._earliestOffset else "KafkaOffsetsInitializer.latest()"}) \\
                .set_value_only_deserializer(SimpleStringSchema("{self.encoding}")) \\
                .build()
            """,
                PyFlinkCodeTemplate.Section.ASSIGNMENTS: f"""
            $inDS.from_source(
                kafkaSource_{self.getUniqueName()}, 
                WatermarkStrategy.for_monotonous_timestamps(), 
                \"kafkaSource_{self.getUniqueName()}\"
            )"""},
                jarDependencies=[PyFlinkJARs.FLINK_KAFKA_CONNECTOR],
                tags=[PyFlinkTags.SOURCE_UNBOUNDED])

            return pyFlinkCode

        return [CompileOpSpecs.getSVDefault(),
                CompileOpSpecs([CompileFramework.PYFLINK],
                               [CompileLanguage.PYTHON],
                               [CompileComputeMode.CPU],
                               CompileParallelism.all(),
                               compileFunction=CodeTemplateCOF(CodeTemplateCOF.Type.SOURCE, getPyFlinkCode))]
