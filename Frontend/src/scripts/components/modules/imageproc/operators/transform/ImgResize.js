import {Component} from "@/scripts/components/Component";
import {IMG_DT, imgSocket} from "@/scripts/components/modules/imageproc";
import {StringControl} from "@/scripts/components/modules/base/controls/StringCtrl";
import {Display} from "@/scripts/components/monitor/Display";

export default class _ImgResize extends Component {
    constructor(pathIdentifier){
        super("ImgResize", "Img Resize", pathIdentifier);
    }

    builder(node) {
        node.scaleX = new StringControl(node, 'scaleX', false, '100%', 'Scale X', 'Value in pixels or percentage.');
        node.scaleY = new StringControl(node, 'scaleY', false, '100%', 'Scale Y', 'Value in pixels or percentage.');

        return this.onBuilderInitialized(node,
            new Display(node, IMG_DT.name),
            [{name: "Image", socket: imgSocket}],
            [{name: "Image", socket: imgSocket}],
            [node.scaleX, node.scaleY]);
    }

    getData(node) {
        return {
            scaleX: node.scaleX.getValue(),
            scaleY: node.scaleY.getValue()
        }
    }

    setData(node, data) {
        node.scaleX.setValue(data.scaleX);
        node.scaleY.setValue(data.scaleY);
    }
}
