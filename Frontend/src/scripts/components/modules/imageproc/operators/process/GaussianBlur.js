import {Component} from "@/scripts/components/Component";
import {IMG_DT, imgSocket} from "@/scripts/components/modules/imageproc";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";
import {Display} from "@/scripts/components/monitor/Display";

export default class _GaussianBlur extends Component {
    constructor(pathIdentifier){
        super("GaussianBlur", "Gaussian Blur", pathIdentifier);
    }

    builder(node) {
        node.kernelX = new NumControl(node, 'kernelX', false, 3, "Kernel Size X", "", 0);
        node.kernelY = new NumControl(node, 'kernelY', false, 3, "Kernel Size Y", "", 0);
        node.sigmaX = new NumControl(node, 'sigmaX', false, 0, "Sigma X", "");
        node.sigmaY = new NumControl(node, 'sigmaY', false, 0, "Sigma Y", "");

        return this.onBuilderInitialized(node,
            new Display(node, IMG_DT.name),
            [{name: "Image", socket: imgSocket}],
            [{name: "Image", socket: imgSocket}],
            [node.kernelX, node.kernelY, node.sigmaX, node.sigmaY]);
    }

    getData(node) {
        return {
            kernelX: node.kernelX.getValue(),
            kernelY: node.kernelY.getValue(),
            sigmaX: node.sigmaX.getValue(),
            sigmaY: node.sigmaY.getValue()
        }
    }

    setData(node, data) {
        node.kernelX.setValue(data.kernelX);
        node.kernelY.setValue(data.kernelY);
        node.sigmaX.setValue(data.sigmaX);
        node.sigmaY.setValue(data.sigmaY);
    }
}
