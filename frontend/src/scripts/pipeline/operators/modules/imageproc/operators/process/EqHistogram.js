import {Definition} from "@/scripts/pipeline/operators/Definition";
import {IMG_DT, imgSocket} from "@/scripts/pipeline/operators/modules/imageproc";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _EqHistogram extends Definition {
    constructor(pathIdentifier){
        super("EqHistogram", "Eq. Histogram", pathIdentifier);
    }

    build(operator) {
        this._construct(operator,
            [new SocketDef(imgSocket)],
            [new SocketDef(imgSocket)],
            [], IMG_DT);
    }
}
