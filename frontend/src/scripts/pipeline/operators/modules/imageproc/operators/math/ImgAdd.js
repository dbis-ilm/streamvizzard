import {Definition} from "@/scripts/pipeline/operators/Definition";
import {IMG_DT, imgSocket} from "@/scripts/pipeline/operators/modules/imageproc";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _ImgAdd extends Definition {
    constructor(pathIdentifier){
        super("ImgAdd", "Img Add", pathIdentifier,
            "Adds a numerical values to each pixel in the input image.");
    }

    build(operator) {
        let value = new NumberParam("value", 0,  null, null, "Value");

        this._construct(operator,
            [new SocketDef(imgSocket)],
            [new SocketDef(imgSocket)],
            [value], IMG_DT);
    }
}
