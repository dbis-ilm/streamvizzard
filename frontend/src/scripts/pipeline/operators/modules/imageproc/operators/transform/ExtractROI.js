import {Definition} from "@/scripts/pipeline/operators/Definition";
import {IMG_DT, imgSocket} from "@/scripts/pipeline/operators/modules/imageproc";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _ExtractROI extends Definition {
    constructor(pathIdentifier){
        super("ExtractROI", "Extract ROI", pathIdentifier);
    }

    build(operator) {
        let x = new NumberParam("x", 0, 0, null, "X");
        let y = new NumberParam("y", 0, 0, null, "Y");
        let w = new NumberParam("w", 100, 1, null, "W");
        let h = new NumberParam("h", 100, 1, null, "H");

        this._construct(operator,
            [new SocketDef(imgSocket)],
            [new SocketDef(imgSocket)],
            [x, y, w, h], IMG_DT);
    }
}
