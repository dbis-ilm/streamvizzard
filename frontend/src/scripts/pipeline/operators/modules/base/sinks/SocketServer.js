import {Definition} from "@/scripts/pipeline/operators/Definition";
import {StringParam} from "@/scripts/pipeline/operators/modules/base/params/StringParam";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";
import {anySocket} from "@/scripts/pipeline/operators/modules";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _SocketServer extends Definition {
    constructor(pathIdentifier){
        super("SocketServer", "Socket Server", pathIdentifier,
            "Sends the bytes data over a socket connection to a client.");
    }

    build(operator) {
        let ip = new StringParam("ip", "127.0.0.1", "Host");
        let port = new NumberParam("port", 9000, 0, null, "Port","The port used for the socket connection");

        this._construct(operator,
            [new SocketDef(anySocket, "Bytes")],
            [],
            [ip, port]);
    }
}
