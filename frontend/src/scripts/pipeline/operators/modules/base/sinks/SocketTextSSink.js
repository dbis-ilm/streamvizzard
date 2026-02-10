import {Definition} from "@/scripts/pipeline/operators/Definition";
import {StringParam} from "@/scripts/pipeline/operators/modules/base/params/StringParam";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";
import {strSocket} from "@/scripts/pipeline/operators/modules/base";
import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _SocketTextSink extends Definition {
    constructor(pathIdentifier){
        super("SocketTextSSink", "Socket Text Server Sink", pathIdentifier);
    }

    build(operator) {
        let ip = new StringParam("ip", "127.0.0.1", "Host");
        let port = new NumberParam("port", 9000, 0, null, "Port","The port used for the socket connection");
        let encoding = new StringParam("encoding", "utf-8", "Encoding", "The encoding used to translate the received bytes to text");

        this._construct(operator,
            [new SocketDef(strSocket)],
            [],
            [ip, port, encoding]);
    }
}
