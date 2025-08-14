import {Control} from "@/scripts/components/Control";
import NumControlTemplate from "@/components/pipeline/controls/NumControlTemplate";

export class NumControl extends Control {

    constructor(node, key, readonly, defaultVal=0, title = "", tooltip = "",
                minVal = -Number.MAX_VALUE, maxVal = Number.MAX_VALUE) {
        super(node, node.editor, key, NumControlTemplate, readonly, defaultVal, title, tooltip);

        this.props["min"] = minVal
        this.props["max"] = maxVal
    }
}