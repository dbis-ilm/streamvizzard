import {Definition} from "@/scripts/pipeline/operators/Definition";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";
import {BoolParam} from "@/scripts/pipeline/operators/modules/base/params/BoolParam";
import {anySocket} from "@/scripts/pipeline/operators/modules";
import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _RandomData extends Definition {
    constructor(pathIdentifier){
        super("RandomData", "Random Data", pathIdentifier,
            "Emits randomly generated data containing a dictionary of {val1: float, val2: int, val3: string, val4: list[float]} for testing purposes.", true);
    }

    build(operator) {
        let limitRate = new BoolParam("limitRate", true, "Limit Rate",
            "If the source should produce tuples in a fixed rate");
        let rate = new NumberParam("rate", 30, 0, null,
            "Rate", "How many data tuples per second are generated.");

        limitRate.onChangeCallback = (val) => { rate.show = val; };

        this._construct(operator,
            [],
            [new SocketDef(anySocket, "Data")],
            [limitRate, rate]);
    }
}
