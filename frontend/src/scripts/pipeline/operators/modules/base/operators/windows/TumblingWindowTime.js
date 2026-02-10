import {Definition} from "@/scripts/pipeline/operators/Definition";
import {anySocket} from "@/scripts/pipeline/operators/modules";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";
import {windowSocket} from "@/scripts/pipeline/operators/modules/base";
import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _TumblingWindowTime extends Definition {
    constructor(pathIdentifier){
        super("TumblingWindowTime", "Tumb. Window Time", pathIdentifier);
    }

    build(operator) {
        let value = new NumberParam("value", 5,0, null, "Interval",
            "The window will evaluate every x seconds and send all collected tuples");

        this._construct(operator,
            [new SocketDef(anySocket)],
            [new SocketDef(windowSocket)],
            [value]);
    }
}
