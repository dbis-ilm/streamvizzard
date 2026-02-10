import {Definition} from "@/scripts/pipeline/operators/Definition";
import {boolSocket, NUMBER_DT} from "@/scripts/pipeline/operators/modules/base";
import {anySocket} from "@/scripts/pipeline/operators/modules";
import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _ToBool extends Definition {
    constructor(pathIdentifier){
        super("ToBool", "To Bool", pathIdentifier);
    }

    build(operator) {
        this._construct(operator,
            [new SocketDef(anySocket)],
            [new SocketDef(boolSocket)],
            [], NUMBER_DT);
    }
}
