import {Component} from "@/scripts/components/Component";
import {IMG_DT, imgSocket} from "@/scripts/components/modules/imageproc";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";
import {Display} from "@/scripts/components/monitor/Display";

export default class _ImgBlend extends Component {
    constructor(pathIdentifier){
        super("ImgBlend", "Img Blend", pathIdentifier);
    }

    builder(node) {
        node.alpha = new NumControl(node, 'alpha', false, 0.5, "Alpha", "", 0);

        return this.onBuilderInitialized(node,
            new Display(node, IMG_DT.name),
            [{name: "Image", socket: imgSocket}, {name: "Image", socket: imgSocket}],
            [{name: "Image", socket: imgSocket}],
            [node.alpha]);
    }

    getData(node) {
        return {
            alpha: node.alpha.getValue()
        }
    }

    setData(node, data) {
        node.alpha.setValue(data.alpha);
    }
}
