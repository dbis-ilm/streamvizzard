import StrControlTemplate from "@/components/templates/controls/StrControlTemplate";
import {Control} from "@/scripts/components/Control";

export class StringControl extends Control {

    constructor(node, key, readonly, defaultVal = "", description, tooltip) {
        super(node, node.editor, key, StrControlTemplate, readonly, defaultVal, description, tooltip);
    }
}