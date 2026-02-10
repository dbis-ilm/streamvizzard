import {Definition} from "@/scripts/pipeline/operators/Definition";
import {IMG_DT, imgSocket} from "@/scripts/pipeline/operators/modules/imageproc";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _ImgBlend extends Definition {
    constructor(pathIdentifier){
        super("ImgBlend", "Img Blend", pathIdentifier);
    }

    build(operator) {
        let alpha = new NumberParam("alpha", 0.5, 0, null, "Alpha");

        this._construct(operator,
            [new SocketDef(imgSocket), new SocketDef(imgSocket)],
            [new SocketDef(imgSocket)],
            [alpha], IMG_DT);
    }
}
