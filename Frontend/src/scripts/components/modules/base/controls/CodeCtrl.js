import CodeControlTemplate from "@/components/templates/controls/CodeControlTemplate";
import {Control} from "@/scripts/components/Control";

export class CodeControl extends Control {

    constructor(node, key, readonly, defaultVal = "", description, tooltip) {
        super(node, node.editor, key, CodeControlTemplate, readonly, defaultVal, description, tooltip);
    }

    setValue(val) {
        this.vueContext.setData(val);
    }
}
