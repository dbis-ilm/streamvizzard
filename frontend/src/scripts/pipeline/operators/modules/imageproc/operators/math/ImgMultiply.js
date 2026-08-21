import {Definition} from "@/scripts/pipeline/operators/Definition";
import {IMG_DT, imgSocket} from "@/scripts/pipeline/operators/modules/imageproc";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _ImgMultiply extends Definition {
    constructor(pathIdentifier){
        super("ImgMultiply", "Img Multiply", pathIdentifier,
            "Multiplies each pixel of the input image by a numerical value.");
    }

    build(operator) {
        let value = new NumberParam("value", 1, null, null, "Factor");

        this._construct(operator,
            [new SocketDef(imgSocket)],
            [new SocketDef(imgSocket)],
            [value], IMG_DT);
    }
}
