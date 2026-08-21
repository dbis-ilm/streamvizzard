import {Definition} from "@/scripts/pipeline/operators/Definition";
import {IMG_DT, imgSocket} from "@/scripts/pipeline/operators/modules/imageproc";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";
import {SelectParam} from "@/scripts/pipeline/operators/modules/base/params/SelectParam";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _Canny extends Definition {
    constructor(pathIdentifier){
        super("Canny", "Canny", pathIdentifier,
            "Detects edges in the input grayscale image.");
    }

    build(operator) {
        let threshold1 = new NumberParam("threshold1", 100, 0, 255, "Threshold 1");
        let threshold2 = new NumberParam("threshold2", 200, 0, 255, "Threshold 2");
        let aperture = new SelectParam("aperture",
            [{title: "3", key: 3}, {title: "5", key: 5},
                {title: "7", key: 7}], 3, "Aperture");

        this._construct(operator,
            [new SocketDef(imgSocket)],
            [new SocketDef(imgSocket)],
            [threshold1, threshold2, aperture], IMG_DT);
    }
}
