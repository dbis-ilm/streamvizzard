import {Definition} from "@/scripts/pipeline/operators/Definition";
import {IMG_DT, imgSocket} from "@/scripts/pipeline/operators/modules/imageproc";
import {SelectParam} from "@/scripts/pipeline/operators/modules/base/params/SelectParam";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _Convert extends Definition {
    constructor(pathIdentifier){
        super("Convert", "Convert", pathIdentifier,
            "Converts the input image into a specified format.");
    }

    build(operator) {
        let mode = new SelectParam("mode",
            [{title: "BGR -> Gray", key: "grayscale"},
                {title: "Gray -> BGR", key: "bgr"},
                {title: "Float32", key: "float32"}],
            "grayscale");

        this._construct(operator,
            [new SocketDef(imgSocket)],
            [new SocketDef(imgSocket)],
            [mode], IMG_DT);
    }
}
