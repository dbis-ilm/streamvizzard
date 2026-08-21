import {Definition} from "@/scripts/pipeline/operators/Definition";
import {IMG_DT, imgSocket} from "@/scripts/pipeline/operators/modules/imageproc";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _WebCam extends Definition {
    constructor(pathIdentifier){
        super("WebCam", "Webcam", pathIdentifier,
            "Streams recorded frames captured by a connected camera device.", true);
    }

    build(operator) {
        let frameRate = new NumberParam("frameRate", 30, 0, null, "Framerate");
        let device = new NumberParam("device", 0, null, null, "Device");

        this._construct(operator,
            [],
            [new SocketDef(imgSocket)],
            [frameRate, device], IMG_DT);
    }
}
