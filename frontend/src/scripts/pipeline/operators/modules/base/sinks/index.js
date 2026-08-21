import TextSocketServer from "@/scripts/pipeline/operators/modules/base/sinks/TextSocketServer";
import SocketServer from "@/scripts/pipeline/operators/modules/base/sinks/SocketServer";
import KafkaSink from "@/scripts/pipeline/operators/modules/base/sinks/KafkaSink";
import FileSink from "@/scripts/pipeline/operators/modules/base/sinks/FileSink";

let getComponents = (pathIdentifier) => {
    return [new FileSink(pathIdentifier), new SocketServer(pathIdentifier),
        new TextSocketServer(pathIdentifier), new KafkaSink(pathIdentifier)];
}

export default {
    FileSink, SocketServer, TextSocketServer, KafkaSink, getComponents
}
