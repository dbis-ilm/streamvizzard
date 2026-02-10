import {Definition} from "@/scripts/pipeline/operators/Definition";
import {imgSocket} from "@/scripts/pipeline/operators/modules/imageproc";

import {SocketDef} from "@/scripts/pipeline/SvSocket";
import {anySocket} from "@/scripts/pipeline/operators/modules";

export default class _CalcHistogram extends Definition {
    constructor(pathIdentifier){
        super("CalcHistogram", "Calc Histogram", pathIdentifier);
    }

    build(operator) {
        this._construct(operator,
            [new SocketDef(imgSocket)],
            [new SocketDef(anySocket)],
            []);
    }
}
