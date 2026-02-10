import {Definition} from "@/scripts/pipeline/operators/Definition";
import {STRING_DT} from "@/scripts/pipeline/operators/modules/base";
import {StringParam} from "@/scripts/pipeline/operators/modules/base/params/StringParam";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";
import {anySocket} from "@/scripts/pipeline/operators/modules";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _SocketTextSource extends Definition {
    constructor(pathIdentifier){
        super("SocketTextSSource", "Socket Text Server Source", pathIdentifier, true);
    }

    build(operator) {
        let ip = new StringParam('ip', '127.0.0.1', "Host");
        let port = new NumberParam('port', 9000, 0, null, "Port","The port used for the socket connection");
        let delimiter = new StringParam('delimiter', "\\n", "Delimiter", "The delimiter used to differentiate between received data elements");
        let encoding = new StringParam('encoding', "utf-8", "Encoding", "The encoding used to translate the received bytes to text");

        this._construct(operator,
            [],
            [new SocketDef(anySocket, "Data")],
            [ip, port, delimiter, encoding], STRING_DT);
    }
}
