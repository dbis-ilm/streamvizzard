import {Component} from "@/scripts/components/Component";
import {Display} from "@/scripts/components/monitor/Display";
import {anySocket} from "@/scripts/components/modules";
import {StringControl} from "@/scripts/components/modules/base/controls/StringCtrl";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";

export default class _LSTMPrediction extends Component {
    constructor(pathIdentifier){
        super("LSTMPredictionSL", "LSTM Prediction", pathIdentifier);
    }

    builder(node) {
        node.modelPath = new StringControl(node, 'srcCtr', false, '', 'Model');
        node.predictSteps = new NumControl(node, "predictSteps", false, 100, 'Steps', '', 0)

        return this.onBuilderInitialized(node,
            new Display(node),
            [{name: anySocket.name, socket: anySocket}],
            [{name: "Predictions", socket: anySocket}],
            [node.modelPath, node.predictSteps]);
    }

    getData(node) {
        return {
            modelPath: node.modelPath.getValue(),
            predictSteps: node.predictSteps.getValue()
        };
    }

    setData(node, data) {
        node.modelPath.setValue(data.modelPath);
        node.predictSteps.setValue(data.predictSteps);
    }
}
