import {Definition} from "@/scripts/pipeline/operators/Definition";
import {IMG_DT, imgSocket} from "@/scripts/pipeline/operators/modules/imageproc";
import {BoolParam} from "@/scripts/pipeline/operators/modules/base/params/BoolParam";
import {StringParam} from "@/scripts/pipeline/operators/modules/base/params/StringParam";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _VideoFile extends Definition {
    constructor(pathIdentifier){
        super("VideoFile", "Video File", pathIdentifier,
            "Loads a video file and streams the individual frames into the pipeline.", true);
    }

    build(operator) {
        let repeat  = new BoolParam("repeat", false, "Loop",
            "Repeats from the start when reaching end of file");
        let limitRate = new BoolParam("limitRate", true, "Limit Rate",
            "If the source should produce tuples in a fixed rate");
        let frameRate = new NumberParam("frameRate", 30, 0, null, "Framerate");
        let path = new StringParam("path", "", "Source");

        limitRate.onChangeCallback = (val) => { frameRate.show = val; };

        this._construct(operator,
            [],
            [new SocketDef(imgSocket)],
            [path, repeat, limitRate, frameRate], IMG_DT);
    }
}
