import {Definition} from "@/scripts/pipeline/operators/Definition";
import {IMG_DT, imgSocket} from "@/scripts/pipeline/operators/modules/imageproc";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";
import {SelectParam} from "@/scripts/pipeline/operators/modules/base/params/SelectParam";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _Threshold extends Definition {
    constructor(pathIdentifier){
        super("Threshold", "Threshold", pathIdentifier,
            "Compares each pixel in the input grayscale image with a threshold and modifies its value based on the mode.");
    }

    build(operator) {
        let threshold = new NumberParam("threshold", 100, 0, 255, "Threshold");
        let maxVal = new NumberParam("maxVal", 255, 0, 255, "Max. Value");
        let mode = new SelectParam("mode",
            [{title: "Binary", key: "binary"}, {title: "Binary Inv", key: "binaryInv"},
                {title: "Trunc", key: "trunc"}, {title: "To Zero", key: "zero"}, {title: "To Zero Inv", key: "zeroInv"}],
            "binary");

        this._construct(operator,
            [new SocketDef(imgSocket)],
            [new SocketDef(imgSocket)],
            [threshold, maxVal, mode], IMG_DT);
    }
}
