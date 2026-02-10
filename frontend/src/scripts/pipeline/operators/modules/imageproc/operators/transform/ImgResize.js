import {Definition} from "@/scripts/pipeline/operators/Definition";
import {IMG_DT, imgSocket} from "@/scripts/pipeline/operators/modules/imageproc";
import {StringParam} from "@/scripts/pipeline/operators/modules/base/params/StringParam";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _ImgResize extends Definition {
    constructor(pathIdentifier){
        super("ImgResize", "Img Resize", pathIdentifier);
    }

    build(operator) {
        let scaleX = new StringParam("scaleX", "100%", "Scale X", "Value in pixels or percentage.");
        let scaleY = new StringParam("scaleY", "100%", "Scale Y", "Value in pixels or percentage.");

        this._construct(operator,
            [new SocketDef(imgSocket)],
            [new SocketDef(imgSocket)],
            [scaleX, scaleY], IMG_DT);
    }
}
