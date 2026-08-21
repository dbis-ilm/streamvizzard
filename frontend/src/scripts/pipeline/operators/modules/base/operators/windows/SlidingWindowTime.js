import {Definition} from "@/scripts/pipeline/operators/Definition";
import {anySocket} from "@/scripts/pipeline/operators/modules";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";
import {windowSocket} from "@/scripts/pipeline/operators/modules/base";
import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _SlidingWindowTime extends Definition {
    constructor(pathIdentifier){
        super("SlidingWindowTime", "Sliding Window Time", pathIdentifier,
            "Emits overlapping batches of input data tuples based on a defined time interval and slide duration.");
    }

    build(operator) {
        let interval = new NumberParam("interval", 10,0, null, "Interval",
            "The window will evaluate every x seconds and send all collected tuples");
        let slide = new NumberParam("slide", 5,0, null, "Slide",
            "Slide duration to move the window interval forward");

        this._construct(operator,
            [new SocketDef(anySocket)],
            [new SocketDef(windowSocket)],
            [interval, slide]);
    }
}
