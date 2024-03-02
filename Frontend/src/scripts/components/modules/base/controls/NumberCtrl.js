import {Control} from "@/scripts/components/Control";
import NumControlTemplate from "@/components/templates/controls/NumControlTemplate";

export class NumControl extends Control {

    constructor(node, key, readonly, defaultVal=0, description = "", tooltip = "",
                minVal = -Number.MAX_VALUE, maxVal = Number.MAX_VALUE) {
        super(node, node.editor, key, NumControlTemplate, readonly, defaultVal, description, tooltip);

        this.props["min"] = minVal
        this.props["max"] = maxVal
    }
}