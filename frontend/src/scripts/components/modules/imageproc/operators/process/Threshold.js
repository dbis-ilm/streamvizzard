import {Component} from "@/scripts/components/Component";
import {IMG_DT, imgSocket} from "@/scripts/components/modules/imageproc";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";
import {SelectControl} from "@/scripts/components/modules/base/controls/SelectCtrl";
import {Display} from "@/scripts/components/monitor/Display";

export default class _Threshold extends Component {
    constructor(pathIdentifier){
        super("Threshold", "Threshold", pathIdentifier);
    }

    builder(node) {
        node.thresholdCtrl = new NumControl(node, 'thresCtrl', false, 100, "Threshold", "", 0, 255);
        node.maxValCtrl = new NumControl(node, 'maxValCtrl', false, 255, "Max. Value", "", 0, 255);
        node.modeCtrl = new SelectControl(node, 'mode',
            false, [{title: "Binary", key: "binary"}, {title: "Binary Inv", key: "binaryInv"},
                {title: "Trunc", key: "trunc"}, {title: "To Zero", key: "zero"}, {title: "To Zero Inv", key: "zeroInv"}], "binary");

        return this.onBuilderInitialized(node,
            new Display(node, IMG_DT.name),
            [{name: "Image", socket: imgSocket}],
            [{name: "Image", socket: imgSocket}],
            [node.thresholdCtrl, node.maxValCtrl, node.modeCtrl]);
    }

    getData(node) {
        return {
            threshold: node.thresholdCtrl.getValue(),
            maxVal: node.maxValCtrl.getValue(),
            mode: node.modeCtrl.getValue()
        }
    }

    setData(node, data) {
        node.thresholdCtrl.setValue(data.threshold);
        node.maxValCtrl.setValue(data.maxVal);
        node.modeCtrl.setValue(data.mode);
    }
}
