import {Definition} from "@/scripts/pipeline/operators/Definition";
import {IMG_DT, imgSocket} from "@/scripts/pipeline/operators/modules/imageproc";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _ImgSplit extends Definition {
    constructor(pathIdentifier) {
        super("ImgSplit", "Img Split", pathIdentifier,
            "Splits the input image into the individual color channels.");
    }

    build(operator) {
        this._construct(operator,
            [new SocketDef(imgSocket)],
            [
                new SocketDef(imgSocket, "B"),
                new SocketDef(imgSocket, "G"),
                new SocketDef(imgSocket, "R"),
                new SocketDef(imgSocket, "A")
            ],[], IMG_DT);
    }
}
