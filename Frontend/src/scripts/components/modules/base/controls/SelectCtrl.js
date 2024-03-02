import SelectControlTemplate from "@/components/templates/controls/SelectControlTemplate";
import {Control} from "@/scripts/components/Control";

export class SelectControl extends Control {

    constructor(node, key, readonly, options, defaultVal="", description = "", tooltip = "") {
        super(node, node.editor, key, SelectControlTemplate, readonly, defaultVal, description, tooltip);

        this.props["options"] = options;
    }

    getValue() {
        return this.vueContext.value.key;
    }

    setValue(key) {
        this.vueContext.value = this.vueContext.options.find(el => el.key === key);
    }
}
