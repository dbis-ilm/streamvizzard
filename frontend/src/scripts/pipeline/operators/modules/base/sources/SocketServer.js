import {Definition} from "@/scripts/pipeline/operators/Definition";
import {StringParam} from "@/scripts/pipeline/operators/modules/base/params/StringParam";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";
import {anySocket} from "@/scripts/pipeline/operators/modules";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _SocketServer extends Definition {
    constructor(pathIdentifier){
        super("SocketServer", "Socket Server", pathIdentifier,
            "Retrieves byte data from a socket client.", true);
    }

    build(operator) {
        let ip = new StringParam("ip", "127.0.0.1", "Host");
        let port = new NumberParam("port", 9000, 0, null, "Port","The port used for the socket connection")
        let maxBytes = new NumberParam("maxBytes", 1024, 0, null,
            "Max Bytes","The amount of bytes the server will fetch from the client in one message / output tuple.")

        this._construct(operator,
            [],
            [new SocketDef(anySocket, "Bytes")],
            [ip, port, maxBytes]);
    }
}
