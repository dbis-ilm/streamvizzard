import {Component} from "@/scripts/components/Component";
import {Display} from "@/scripts/components/monitor/Display";
import {StringControl} from "@/scripts/components/modules/base/controls/StringCtrl";
import {numSocket} from "@/scripts/components/modules/base";
import {imgSocket} from "@/scripts/components/modules/imageproc";

export default class _CNNPrediction extends Component {
    constructor(pathIdentifier){
        super("CNNPredictionSL", "CNN Prediction", pathIdentifier);
    }

    builder(node) {
        node.modelPath = new StringControl(node, 'srcCtr', false, '', "Model");

        return this.onBuilderInitialized(node,
            new Display(node),
            [{name: imgSocket.name, socket: imgSocket}],
            [{name: "Prediction", socket: numSocket}],
            [node.modelPath]);
    }

    getData(node) {
        return {
            modelPath: node.modelPath.getValue()
        };
    }

    setData(node, data) {
        node.modelPath.setValue(data.modelPath);
    }
}
