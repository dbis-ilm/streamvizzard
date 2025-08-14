import {Component} from "@/scripts/components/Component";
import {IMG_DT, imgSocket} from "@/scripts/components/modules/imageproc";
import {Display} from "@/scripts/components/monitor/Display";

export default class _ImgSplit extends Component {
    constructor(pathIdentifier){
        super("ImgSplit", "Img Split", pathIdentifier);
    }

    builder(node) {
        return this.onBuilderInitialized(node,
            new Display(node, IMG_DT),
            [{name: "Image", socket: imgSocket}],
            [{name: "B", socket: imgSocket}, {name: "G", socket: imgSocket}, {name: "R", socket: imgSocket}, {name: "A", socket: imgSocket}],
            []);
    }
}
