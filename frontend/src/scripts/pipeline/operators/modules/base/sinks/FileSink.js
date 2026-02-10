import {Definition} from "@/scripts/pipeline/operators/Definition";
import {StringParam} from "@/scripts/pipeline/operators/modules/base/params/StringParam";
import {strSocket} from "@/scripts/pipeline/operators/modules/base";

import {SocketDef} from "@/scripts/pipeline/SvSocket";

export default class _FileSink extends Definition {
    constructor(pathIdentifier){
        super("FileSink", "File Sink", pathIdentifier);
    }

    build(operator) {
        let path = new StringParam("path", "", "Path");

        this._construct(operator,
            [new SocketDef(strSocket)],
            [],
            [path]);
    }
}
