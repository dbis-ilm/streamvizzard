import {Definition} from "@/scripts/pipeline/operators/Definition";
import {NUMBER_DT, numSocket} from "@/scripts/pipeline/operators/modules/base";
import {anySocket} from "@/scripts/pipeline/operators/modules";
import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _ToInt extends Definition {
    constructor(pathIdentifier) {
        super("ToInt", "To Int", pathIdentifier);
    }

    build(operator) {
        this._construct(operator,
            [new SocketDef(anySocket)],
            [new SocketDef(numSocket)],
            [], NUMBER_DT);
    }
}
