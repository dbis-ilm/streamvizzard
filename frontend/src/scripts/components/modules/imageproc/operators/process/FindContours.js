import {Component} from "@/scripts/components/Component";
import {IMG_DT, imgSocket} from "@/scripts/components/modules/imageproc";
import {SelectControl} from "@/scripts/components/modules/base/controls/SelectCtrl";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";
import {Display} from "@/scripts/components/monitor/Display";

export default class _FindContours extends Component {
    constructor(pathIdentifier){
        super("FindContours", "Find Contours", pathIdentifier);
    }

    builder(node) {
        node.mode = new SelectControl(node, 'mode',
            false, [{title: "List", key: 0}, {title: "Tree", key: 1},
                {title: "CComp", key: 2}, {title: "External", key: 3}, {title: "FloodFill", key: 4}],
            0, "Mode");
        node.method = new SelectControl(node, 'method',
            false, [{title: "Approx None", key: 0}, {title: "Approx Simple", key: 1},
                {title: "Approx TC89_L1", key: 2}, {title: "Approx TC89_KCOS", key: 3}],
            0, "Method");
        node.drawThickness = new NumControl(node, 'drawThickness', false, 1,
            "Contour Thickness", "Thickness of lines used to draw the contours on the image", 1);

        return this.onBuilderInitialized(node,
            new Display(node, IMG_DT.name),
            [{name: "Image", socket: imgSocket}],
            [{name: "Image", socket: imgSocket}, {name: "Contours", socket: imgSocket}, {name: "Hierarchy", socket: imgSocket}],
            [node.mode, node.method, node.drawThickness]);
    }

    getData(node) {
        return {
            mode: node.mode.getValue(),
            method: node.method.getValue(),
            drawThickness: node.drawThickness.getValue()
        }
    }

    setData(node, data) {
        node.mode.setValue(data.mode);
        node.method.setValue(data.method);
        node.drawThickness.setValue(data.drawThickness);
    }
}
