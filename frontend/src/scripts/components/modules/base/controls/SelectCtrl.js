import SelectControlTemplate from "@/components/pipeline/controls/SelectControlTemplate";
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
        let option = this.vueContext.options.find(el => el.key === key);
        if(option != null) this.vueContext.setData(option);
    }
}
