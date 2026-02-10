import {Definition} from "@/scripts/pipeline/operators/Definition";
import {anySocket} from "@/scripts/pipeline/operators/modules";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";
import {windowSocket} from "@/scripts/pipeline/operators/modules/base";
import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _TumblingWindowCount extends Definition {
    constructor(pathIdentifier){
        super("TumblingWindowCount", "Tumb. Window Count", pathIdentifier);
    }

    build(operator) {
        let value = new NumberParam("value", 5,0, null, "Count");

        this._construct(operator,
            [new SocketDef(anySocket)],
            [new SocketDef(windowSocket)],
            [value]);
    }
}
