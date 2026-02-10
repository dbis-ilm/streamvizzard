import StringParamTemplate from "@/components/pipeline/operator/params/StringParamTemplate.vue";
import {Param} from "@/scripts/pipeline/operators/Param";

/** @typedef {import('./StringParam.js').StringParam} StringParam */

export class StringParam extends Param {
    /** @param {String} key
     * @param {String} defaultVal
     * @param {String} title
     * @param {String|null} tooltip **/
    constructor(key, defaultVal = "", title, tooltip) {
        super(key, defaultVal, title, tooltip);
    }

    getTemplate() {
        return StringParamTemplate;
    }
}