import {Definition} from "@/scripts/pipeline/operators/Definition";
import {arraySocket, STRING_DT, strSocket} from "@/scripts/pipeline/operators/modules/base";
import {StringParam} from "@/scripts/pipeline/operators/modules/base/params/StringParam";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _StringSplit extends Definition {
    constructor(pathIdentifier){
        super("StringSplit", "String Split", pathIdentifier,
            "Splits the input String by the specified delimiter into a tuple of individual elements.");
    }

    build(operator) {
        let delimiter = new StringParam("delimiter", ",","Delim");

        this._construct(operator,
            [new SocketDef(strSocket)],
            [new SocketDef(arraySocket)],
            [delimiter], STRING_DT);
    }
}
