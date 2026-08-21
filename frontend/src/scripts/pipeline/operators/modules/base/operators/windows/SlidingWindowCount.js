import {Definition} from "@/scripts/pipeline/operators/Definition";
import {anySocket} from "@/scripts/pipeline/operators/modules";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";
import {windowSocket} from "@/scripts/pipeline/operators/modules/base";
import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _SlidingWindowCount extends Definition {
    constructor(pathIdentifier){
        super("SlidingWindowCount", "Sliding Window Count", pathIdentifier,
            "Emits overlapping batches of input data tuples based on a defined number of elements and slide amount.");
    }

    build(operator) {
        let count = new NumberParam("count", 10,0, null, "Count", "How many tuples should be contained in each window.");
        let slide = new NumberParam("slide", 5,0, null, "Slide", "Step size to slide the window forward.");

        this._construct(operator,
            [new SocketDef(anySocket)],
            [new SocketDef(windowSocket)],
            [count, slide]);
    }
}
