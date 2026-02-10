import {Definition} from "@/scripts/pipeline/operators/Definition";
import {strSocket} from "@/scripts/pipeline/operators/modules/base";

import {SocketDef} from "@/scripts/pipeline/SvSocket";
import {anySocket} from "@/scripts/pipeline/operators/modules";

export default class _SerializeJSON extends Definition {
    constructor(pathIdentifier){
        super("SerializeJSON", "Serialize JSON", pathIdentifier);
    }

    build(operator) {
        this._construct(operator,
            [new SocketDef(anySocket, "Data")],
            [new SocketDef(strSocket)],
            []);
    }
}
