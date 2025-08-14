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
        node.repeat  = new BoolControl(node, 'repeat', false, 'Loop',
            'Repeats from the start when reaching end of file');
        node.limitRate = new BoolControl(node, 'limitRate', false, 'Limit Rate',
            'If the source should produce tuples in a fixed rate', true);
        node.frameRate = new NumControl(node, 'frameRate', false, 30, "Framerate", "", 0);
        node.path = new StringControl(node, 'path', false, '', "Source");

        node.limitRate.onChangeCallback = (val) => {
            node.frameRate.show = val;
        };

        return this.onBuilderInitialized(node,
            new Display(node, IMG_DT.name),
            [],
            [{name: "Image", socket: imgSocket}],
            [node.path, node.repeat, node.limitRate, node.frameRate]);
    }
}
