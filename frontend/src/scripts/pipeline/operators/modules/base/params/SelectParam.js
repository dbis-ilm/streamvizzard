import SelectParamTemplate from "@/components/pipeline/operator/params/SelectParamTemplate.vue";
import {Param} from "@/scripts/pipeline/operators/Param";

/** @typedef {import('./SelectParam.js').SelectParam} SelectParam */

export class SelectParam extends Param {
    /** @param {String} key
     * @param {Array} options
     * @param {any} defaultVal
     * @param {String} title
     * @param {String|null} tooltip **/
    constructor(key, options, defaultVal, title = "", tooltip = "") {
        super(key, defaultVal, title, tooltip);

        this.options = options;
    }

    getTemplate() {
        return SelectParamTemplate;
    }
}
