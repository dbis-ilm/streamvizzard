import {Component} from "@/scripts/components/Component";
import {IMG_DT, imgSocket} from "@/scripts/components/modules/imageproc";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";
import {Display} from "@/scripts/components/monitor/Display";

export default class _WebCam extends Component {
    constructor(pathIdentifier){
        super("WebCam", "Webcam", pathIdentifier, true);
    }

    builder(node) {
        node.frameRateCtrl = new NumControl(node, 'frameRateCtrl', false, 30, "Framerate", "", 0)
        node.device = new NumControl(node, 'device', false, 0, "Device")

        return this.onBuilderInitialized(node,
            new Display(node, IMG_DT.name),
            [],
            [{name: "Image", socket: imgSocket}],
            [node.frameRateCtrl, node.device]);
    }

    getData(node) {
        return {
            frameRate: node.frameRateCtrl.getValue(),
            device: node.device.getValue()
        }
    }

    setData(node, data) {
        node.frameRateCtrl.setValue(data.frameRate);
        node.device.setValue(data.device);
    }
}
