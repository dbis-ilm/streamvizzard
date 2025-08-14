import {Component} from "@/scripts/components/Component";
import {IMG_DT, imgSocket} from "@/scripts/components/modules/imageproc";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";
import {Display} from "@/scripts/components/monitor/Display";

export default class _ImgAdd extends Component {
    constructor(pathIdentifier){
        super("ImgAdd", "Img Add", pathIdentifier);
    }

    builder(node) {
        node.valueCtrl = new NumControl(node, 'value', false, 0, "Value", "");

        return this.onBuilderInitialized(node,
            new Display(node, IMG_DT.name),
            [{name: "Image", socket: imgSocket}],
            [{name: "Image", socket: imgSocket}],
            [node.valueCtrl]);
    }

    getData(node) {
        return {
            value: node.valueCtrl.getValue()
        }
    }

    setData(node, data) {
        node.valueCtrl.setValue(data.value);
    }
}


