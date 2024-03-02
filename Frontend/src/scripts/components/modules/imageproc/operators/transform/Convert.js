import {Component} from "@/scripts/components/Component";
import {IMG_DT, imgSocket} from "@/scripts/components/modules/imageproc";
import {SelectControl} from "@/scripts/components/modules/base/controls/SelectCtrl";
import {Display} from "@/scripts/components/monitor/Display";

export default class _Convert extends Component {
    constructor(pathIdentifier){
        super("Convert", "Convert", pathIdentifier);
    }

    builder(node) {
        node.selectCtrl = new SelectControl(node, 'mode',
            false, [{title: "BGR -> Gray", key: "grayscale"},
                {title: "Gray -> BGR", key: "bgr"},
                {title: "Float32", key: "float32"}], "grayscale");

        return this.onBuilderInitialized(node,
            new Display(node, IMG_DT.name),
            [{name: "Image", socket: imgSocket}],
            [{name: "Image", socket: imgSocket}],
            [node.selectCtrl]);
    }

    getData(node) {
        return {
            mode: node.selectCtrl.getValue()
        }
    }

    setData(node, data) {
        node.selectCtrl.setValue(data.mode);
    }
}
