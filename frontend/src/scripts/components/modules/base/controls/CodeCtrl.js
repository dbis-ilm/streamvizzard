import CodeControlTemplate from "@/components/pipeline/controls/CodeControlTemplate";
import {Control} from "@/scripts/components/Control";

export class CodeControl extends Control {
    static CodeType = {
        UDF: "UDF",
        UDO: "UDO",
        FILTER: "FILTER"
    };

    constructor(node, key, readonly, codeType, defaultVal = "", description, tooltip) {
        super(node, node.editor, key, CodeControlTemplate, readonly, defaultVal, description, tooltip);

        this.props["type"] = codeType;
    }
}
