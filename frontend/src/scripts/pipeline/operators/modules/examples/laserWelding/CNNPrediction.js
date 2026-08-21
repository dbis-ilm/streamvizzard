import {Definition} from "@/scripts/pipeline/operators/Definition";
import {StringParam} from "@/scripts/pipeline/operators/modules/base/params/StringParam";
import {anySocket} from "@/scripts/pipeline/operators/modules";
import {imgSocket} from "@/scripts/pipeline/operators/modules/imageproc";
import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _CNNPrediction extends Definition {
    constructor(pathIdentifier){
        super("CNNPredictionSL", "CNN Prediction", pathIdentifier,
            "Predicts the laser-welding seam break based on LWIR input images of the emerging weld.");
    }

    build(operator) {
        let modelPath = new StringParam("modelPath", "", "Model");

        this._construct(operator,
            [new SocketDef(imgSocket)],
            [new SocketDef(anySocket, "Prediction")],
            [modelPath]);
    }
}
