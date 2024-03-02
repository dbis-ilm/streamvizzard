import {Component} from "@/scripts/components/Component";
import {IMG_DT, imgSocket} from "@/scripts/components/modules/imageproc";
import {Display} from "@/scripts/components/monitor/Display";
import {strSocket} from "@/scripts/components/modules/base";
import {StringControl} from "@/scripts/components/modules/base/controls/StringCtrl";

export default class _ImgLoad extends Component {
    constructor(pathIdentifier){
        super("ImgLoad", "Img Load", pathIdentifier);
    }

    builder(node) {
        node.flags = new StringControl(node, 'flags', false, "", 'Flags', 'Given in OpenCV flag codes');

        return this.onBuilderInitialized(node,
            new Display(node, IMG_DT.name),
            [{name: "Path", socket: strSocket}],
            [{name: "Image", socket: imgSocket}],
            [node.flags]);
    }

    getData(node) {
        return {
            flags: node.flags.getValue()
        }
    }

    setData(node, data) {
        node.flags.setValue(data.flags);
    }
}
