import {Definition} from "@/scripts/pipeline/operators/Definition";
import {arraySocket, windowSocket} from "@/scripts/pipeline/operators/modules/base";
import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _WindowCollect extends Definition {
    constructor(pathIdentifier){
        super("WindowCollect", "Window Collect", pathIdentifier,
            "Takes a window of data tuples as an input and emits a combined list of their individual values.");
    }

    build(operator) {
        this._construct(operator,
            [new SocketDef(windowSocket)],
            [new SocketDef(arraySocket)],
            []);
    }
}
