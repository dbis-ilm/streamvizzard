import {Definition} from "@/scripts/pipeline/operators/Definition";
import {STRING_DT, strSocket} from "@/scripts/pipeline/operators/modules/base";
import {StringParam} from "@/scripts/pipeline/operators/modules/base/params/StringParam";
import {NumberParam} from "@/scripts/pipeline/operators/modules/base/params/NumberParam";
import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _HTTPGet extends Definition {
    constructor(pathIdentifier){
        super("HTTPGet", "HTTP Get", pathIdentifier, true);
    }

    build(operator) {
        let url = new StringParam("url", "", "URL");
        let rate = new NumberParam('rate', 30, 0,  null,
            "Rate", "How many requests per second are done");

        this._construct(operator,
            [],
            [new SocketDef(strSocket, "Data")],
            [url, rate], STRING_DT);
    }
}
