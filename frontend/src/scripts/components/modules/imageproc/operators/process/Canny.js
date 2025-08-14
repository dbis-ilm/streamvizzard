import {Component} from "@/scripts/components/Component";
import {IMG_DT, imgSocket} from "@/scripts/components/modules/imageproc";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";
import {SelectControl} from "@/scripts/components/modules/base/controls/SelectCtrl";
import {Display} from "@/scripts/components/monitor/Display";

export default class _Canny extends Component {
    constructor(pathIdentifier){
        super("Canny", "Canny", pathIdentifier);
    }

    builder(node) {
        node.threshold1Ctrl = new NumControl(node, 'thres1', false, 100, "Threshold 1", "", 0, 255);
        node.threshold2Ctrl = new NumControl(node, 'thres2', false, 200, "Threshold 2", "", 0, 255);
        node.aperture = new SelectControl(node, 'aperture',
            false, [{title: "3", key: 3}, {title: "5", key: 5},
                {title: "7", key: 7}], 3, "Aperture");

        return this.onBuilderInitialized(node,
            new Display(node, IMG_DT.name),
            [{name: "Image", socket: imgSocket}],
            [{name: "Image", socket: imgSocket}],
            [node.threshold1Ctrl, node.threshold2Ctrl, node.aperture]);
    }

    getData(node) {
        return {
            threshold1: node.threshold1Ctrl.getValue(),
            threshold2: node.threshold2Ctrl.getValue(),
            aperture: node.aperture.getValue()
        }
    }

    setData(node, data) {
        node.threshold1Ctrl.setValue(data.threshold1);
        node.threshold2Ctrl.setValue(data.threshold2);
        node.aperture.setValue(data.aperture);
    }
}
