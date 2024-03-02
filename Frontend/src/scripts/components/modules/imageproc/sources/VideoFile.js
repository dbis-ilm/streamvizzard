import {Component} from "@/scripts/components/Component";
import {IMG_DT, imgSocket} from "@/scripts/components/modules/imageproc";
import {BoolControl} from "@/scripts/components/modules/base/controls/BoolCtrl";
import {StringControl} from "@/scripts/components/modules/base/controls/StringCtrl";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";
import {Display} from "@/scripts/components/monitor/Display";

export default class _VideoFile extends Component {
    constructor(pathIdentifier){
        super("VideoFile", "Video File", pathIdentifier, true);
    }

    builder(node) {
        node.repeatCtrl  = new BoolControl(node, 'boolCtrl', false, 'Loop',
            'Repeats from the start when reaching end of file');
        node.frameRateCtrl = new NumControl(node, 'frameRateCtrl', false, 30, "Framerate", "", 0)
        node.srcCtrl = new StringControl(node, 'srcCtr', false, 'filepath', "Source");

        return this.onBuilderInitialized(node,
            new Display(node, IMG_DT.name),
            [],
            [{name: "Image", socket: imgSocket}],
            [node.srcCtrl, node.repeatCtrl, node.frameRateCtrl]);
    }

    getData(node) {
        return {
            path: node.srcCtrl.getValue(),
            repeat: node.repeatCtrl.getValue() ? 1 : 0,
            frameRate: node.frameRateCtrl.getValue()
        }
    }

    setData(node, data) {
        node.srcCtrl.setValue(data.path);
        node.repeatCtrl.setValue(data.repeat === 1);
        node.frameRateCtrl.setValue(data.frameRate);
    }
}
