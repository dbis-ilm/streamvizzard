import {Definition} from "@/scripts/pipeline/operators/Definition";
import {anySocket} from "@/scripts/pipeline/operators/modules";
import {StringParam} from "@/scripts/pipeline/operators/modules/base/params/StringParam";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _LSTMPrediction extends Definition {
    constructor(pathIdentifier){
        super("LSTMPredictionSL", "LSTM Prediction", pathIdentifier);
    }

    build(operator) {
        let modelPath = new StringParam("modelPath", "", "Model");
        let predictSteps = new NumberParam("predictSteps", 100, 0, null, "Steps");

        this._construct(operator,
            [new SocketDef(anySocket)],
            [new SocketDef(anySocket, "Prediction")],
            [modelPath, predictSteps]);
    }
}
