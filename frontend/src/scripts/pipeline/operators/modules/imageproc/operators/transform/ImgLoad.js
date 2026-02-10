import {Definition} from "@/scripts/pipeline/operators/Definition";
import {IMG_DT, imgSocket} from "@/scripts/pipeline/operators/modules/imageproc";
import {strSocket} from "@/scripts/pipeline/operators/modules/base";
import {StringParam} from "@/scripts/pipeline/operators/modules/base/params/StringParam";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _ImgLoad extends Definition {
    constructor(pathIdentifier){
        super("ImgLoad", "Img Load", pathIdentifier);
    }

    build(operator) {
        let flags = new StringParam("flags", "", "Flags", "Given in OpenCV flag codes");

        this._construct(operator,
            [new SocketDef(strSocket, "Path")],
            [new SocketDef(imgSocket)],
            [flags], IMG_DT);
    }
}
