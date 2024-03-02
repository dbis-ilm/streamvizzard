import BoolControlTemplate from "@/components/templates/controls/BoolControlTemplate";
import {Control} from "@/scripts/components/Control";

export class BoolControl extends Control {

    constructor(node, key, readonly, description, tooltip, defaultVal = false) {
        super(node, node.editor, key, BoolControlTemplate, readonly, defaultVal, description, tooltip);
    }
}
