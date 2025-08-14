import {Component} from "@/scripts/components/Component";
import {IMG_DT, imgSocket} from "@/scripts/components/modules/imageproc";
import {Display} from "@/scripts/components/monitor/Display";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";

export default class _ExtractROI extends Component {
    constructor(pathIdentifier){
        super("ExtractROI", "Extract ROI", pathIdentifier);
    }

    builder(node) {
        node.x = new NumControl(node, 'x', false, 0, "X", "", 0);
        node.y = new NumControl(node, 'y', false, 0, "Y", "", 0);
        node.w = new NumControl(node, 'w', false, 100, "W", "", 1);
        node.h = new NumControl(node, 'h', false, 100, "H", "", 1);

        return this.onBuilderInitialized(node,
            new Display(node, IMG_DT.name),
            [{name: "Image", socket: imgSocket}],
            [{name: "Image", socket: imgSocket}],
            [node.x, node.y, node.w, node.h]);
    }

    getData(node) {
        return {
            x: node.x.getValue(),
            y: node.y.getValue(),
            w: node.w.getValue(),
            h: node.h.getValue()
        }
    }

    setData(node, data) {
        node.x.setValue(data.x);
        node.y.setValue(data.y);
        node.w.setValue(data.w);
        node.h.setValue(data.h);
    }
}
