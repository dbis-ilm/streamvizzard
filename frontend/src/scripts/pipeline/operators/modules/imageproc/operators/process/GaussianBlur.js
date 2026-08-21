import {Definition} from "@/scripts/pipeline/operators/Definition";
import {IMG_DT, imgSocket} from "@/scripts/pipeline/operators/modules/imageproc";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _GaussianBlur extends Definition {
    constructor(pathIdentifier){
        super("GaussianBlur", "Gaussian Blur", pathIdentifier,
            "Smoothens the input image via a Gaussian kernel.");
    }

    build(operator) {
        let kernelX = new NumberParam("kernelX", 3, 0, null, "Kernel Size X");
        let kernelY = new NumberParam("kernelY", 3, 0, null, "Kernel Size Y");
        let sigmaX = new NumberParam("sigmaX", 0, null, null, "Sigma X");
        let sigmaY = new NumberParam("sigmaY", 0, null, null, "Sigma Y");

        this._construct(operator,
            [new SocketDef(imgSocket)],
            [new SocketDef(imgSocket)],
            [kernelX, kernelY, sigmaX, sigmaY], IMG_DT);
    }
}
