import TextFile from "@/scripts/pipeline/operators/modules/base/sources/TextFile";
import HTTPGet from "@/scripts/pipeline/operators/modules/base/sources/HTTPGet";
import ReadFolder from "@/scripts/pipeline/operators/modules/base/sources/ReadFolder";
import SocketServer from "@/scripts/pipeline/operators/modules/base/sources/SocketServer";
import SocketTextServer from "@/scripts/pipeline/operators/modules/base/sources/TextSocketServer";
import UDS from "@/scripts/pipeline/operators/modules/base/sources/UDS";
import KafkaSource from "@/scripts/pipeline/operators/modules/base/sources/KafkaSource";
import RandomData from "@/scripts/pipeline/operators/modules/base/sources/RandomData";

let getComponents = (pathIdentifier) => {
    return [new TextFile(pathIdentifier), new HTTPGet(pathIdentifier),
    new ReadFolder(pathIdentifier), new SocketServer(pathIdentifier), new RandomData(pathIdentifier),
        new SocketTextServer(pathIdentifier), new UDS(pathIdentifier), new KafkaSource(pathIdentifier),];
}

export default {
    TextFile, HTTPGet, ReadFolder, SocketServer, SocketTextServer, UDS, KafkaSource, RandomData, getComponents
}
