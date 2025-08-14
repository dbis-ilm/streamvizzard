import {Component} from "@/scripts/components/Component";
import {Display} from "@/scripts/components/monitor/Display";
import {anySocket} from "@/scripts/components/modules";
import {SelectControl} from "@/scripts/components/modules/base/controls/SelectCtrl";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";


export default class _AnomalyDetection extends Component {
    constructor(pathIdentifier){
        super("AnomalyDetection", "Anomaly Detection", pathIdentifier);
    }

    builder(node) {
        node.upperQuantile = new NumControl(node, 'upperQuantile', false, 75, "Quantile Up", "The upper quantile for the anomaly detection, the lower the more values are outside the valid range.");
        node.lowerQuantile = new NumControl(node, 'lowerQuantile', false, 25, "Quantile Low", "The lower quantile for the anomaly detection, the higher the more values are outside the valid range.");
        node.windowSize = new NumControl(node, 'windowSize', false, 10, "Window Size", "The amount of tuples to consider for calculating the local replacement.");
        node.mode = new SelectControl(node, 'mode',
            false, [{title: "Mode", key: "mode"},
            {title: "Mean", key: "mean"},
                {title: "Median", key: "median"},
                {title: "Remove", key: "remove"}], "mean", "Replacement");
        return this.onBuilderInitialized(node,
            new Display(node),
            [{name: "Any", socket: anySocket}],
            [{name: "Cleaned", socket: anySocket}, {name: "Anomalies", socket: anySocket}],
            [node.mode, node.upperQuantile, node.lowerQuantile, node.windowSize]);
    }
}
