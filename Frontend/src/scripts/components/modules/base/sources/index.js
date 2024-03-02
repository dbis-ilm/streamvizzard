import TextFile from "@/scripts/components/modules/base/sources/TextFile";
import HTTPGet from "@/scripts/components/modules/base/sources/HTTPGet";
import ReadFolder from "@/scripts/components/modules/base/sources/ReadFolder";
import SocketServer from "@/scripts/components/modules/base/sources/SocketServer";
import UDS from "@/scripts/components/modules/base/sources/UDS";

let getComponents = (pathIdentifier) => {
    return [new TextFile(pathIdentifier), new HTTPGet(pathIdentifier),
    new ReadFolder(pathIdentifier), new SocketServer(pathIdentifier),
    new UDS(pathIdentifier)];
}

export default {
    TextFile, HTTPGet, ReadFolder, SocketServer, UDS, getComponents
}
