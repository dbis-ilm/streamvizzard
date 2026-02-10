import SocketTextSSink from "@/scripts/pipeline/operators/modules/base/sinks/SocketTextSSink";
import KafkaSink from "@/scripts/pipeline/operators/modules/base/sinks/KafkaSink";
import FileSink from "@/scripts/pipeline/operators/modules/base/sinks/FileSink";

let getComponents = (pathIdentifier) => {
    return [new FileSink(pathIdentifier), new SocketTextSSink(pathIdentifier), new KafkaSink(pathIdentifier)];
}

export default {
    FileSink, SocketTextSSink, KafkaSink, getComponents
}
