import {Definition} from "@/scripts/pipeline/operators/Definition";
import {IMG_DT, imgSocket} from "@/scripts/pipeline/operators/modules/imageproc";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _ImgMerge extends Definition {
    constructor(pathIdentifier) {
        super("ImgMerge", "Img Merge", pathIdentifier,
            "Merges the individual colors channels into one combined image.");
    }

    build(operator) {
        this._construct(operator,
            [
                new SocketDef(imgSocket, "B"),
                new SocketDef(imgSocket, "G"),
                new SocketDef(imgSocket, "R"),
                new SocketDef(imgSocket, "A")
            ],
            [new SocketDef(imgSocket)],
            [], IMG_DT);
    }
}
