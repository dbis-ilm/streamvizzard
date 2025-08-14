import StrControlTemplate from "@/components/pipeline/controls/StrControlTemplate";
import {Control} from "@/scripts/components/Control";

export class StringControl extends Control {

    constructor(node, key, readonly, defaultVal = "", title, tooltip) {
        super(node, node.editor, key, StrControlTemplate, readonly, defaultVal, title, tooltip);
    }
}