import SocketTextSSink from "@/scripts/components/modules/base/sinks/SocketTextSSink";
import KafkaSink from "@/scripts/components/modules/base/sinks/KafkaSink";
import FileSink from "@/scripts/components/modules/base/sinks/FileSink";

let getComponents = (pathIdentifier) => {
    return [new FileSink(pathIdentifier), new SocketTextSSink(pathIdentifier), new KafkaSink(pathIdentifier)];
}

export default {
    FileSink, SocketTextSSink, KafkaSink, getComponents
}
