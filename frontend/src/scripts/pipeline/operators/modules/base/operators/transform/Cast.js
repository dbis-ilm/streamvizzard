import {Definition} from "@/scripts/pipeline/operators/Definition";
import {anySocket} from "@/scripts/pipeline/operators/modules";
import {SocketDef} from "@/scripts/pipeline/SvSocket";
import {SelectParam} from "@/scripts/pipeline/operators/modules/base/params/SelectParam";

export default class _Cast extends Definition {
    constructor(pathIdentifier){
        super("Cast", "Cast", pathIdentifier,
            "Casts the input data into a specified format.");
    }

    build(operator) {
        let mode = new SelectParam("mode",
            [
                {title: "String", key: "string"},
                {title: "Boolean", key: "bool"},
                {title: "Integer", key: "int"},
                {title: "Float", key: "float"},
            ], "string", "Mode");

        this._construct(operator,
            [new SocketDef(anySocket)],
            [new SocketDef(anySocket)],
            [mode]);
    }
}
