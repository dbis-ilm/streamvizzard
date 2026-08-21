import {Definition} from "@/scripts/pipeline/operators/Definition";
import {anySocket} from "@/scripts/pipeline/operators/modules";
import {SelectParam} from "@/scripts/pipeline/operators/modules/base/params/SelectParam";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";

import {SocketDef} from "@/scripts/pipeline/SvSocket";


export default class _AnomalyDetection extends Definition {
    constructor(pathIdentifier){
        super("AnomalyDetection", "Anomaly Detection", pathIdentifier,
            "Detects anomalies in the input data (list of numerical elements) and potentially resolves them.");
    }

    build(operator) {
        let upperQuantile = new NumberParam("upperQuantile", 75, 0, 100,
            "Quantile Up", "The upper quantile for the anomaly detection, the lower the more values are outside the valid range.");
        let lowerQuantile = new NumberParam("lowerQuantile", 25, 0, 100,
            "Quantile Low", "The lower quantile for the anomaly detection, the higher the more values are outside the valid range.");
        let windowSize = new NumberParam("windowSize", 10, 0, null,
            "Window Size", "The amount of tuples to consider for calculating the local replacement.");
        let mode = new SelectParam("mode",
            [{title: "Mode", key: "mode"},
                {title: "Mean", key: "mean"},
                {title: "Median", key: "median"},
                {title: "Remove", key: "remove"}],
            "mean", "Replacement");

        this._construct(operator,
            [new SocketDef(anySocket)],
            [new SocketDef(anySocket, "Cleaned"), new SocketDef(anySocket, "Anomalies")],
            [mode, upperQuantile, lowerQuantile, windowSize]);
    }
}
