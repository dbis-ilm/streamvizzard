import {Definition} from "@/scripts/pipeline/operators/Definition";
import {IMG_DT, imgSocket} from "@/scripts/pipeline/operators/modules/imageproc";
import {SelectParam} from "@/scripts/pipeline/operators/modules/base/params/SelectParam";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _FindContours extends Definition {
    constructor(pathIdentifier){
        super("FindContours", "Find Contours", pathIdentifier);
    }

    build(operator) {
        let mode = new SelectParam('mode',
            [{title: "List", key: 0}, {title: "Tree", key: 1},
                {title: "CComp", key: 2}, {title: "External", key: 3}, {title: "FloodFill", key: 4}],
            0, "Mode");
        let method = new SelectParam('method',
            [{title: "Approx None", key: 0}, {title: "Approx Simple", key: 1},
                {title: "Approx TC89_L1", key: 2}, {title: "Approx TC89_KCOS", key: 3}],
            0, "Method");
        let drawThickness = new NumberParam('drawThickness', 1, 1, null,
            "Contour Thickness", "Thickness of lines used to draw the contours on the image");

        this._construct(operator,
            [new SocketDef(imgSocket)],
            [new SocketDef(imgSocket), new SocketDef(imgSocket, "Contours"), new SocketDef(imgSocket, "Hierarchy")],
            [mode, method, drawThickness], IMG_DT);
    }
}
