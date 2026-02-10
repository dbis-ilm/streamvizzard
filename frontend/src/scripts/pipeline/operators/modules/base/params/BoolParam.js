import BoolParamTemplate from "@/components/pipeline/operator/params/BoolParamTemplate.vue";
import {Param} from "@/scripts/pipeline/operators/Param";

export class BoolParam extends Param {
    /** @param {String} key
     * @param {any} defaultVal
     * @param {String} title
     * @param {String|null} tooltip **/
    constructor(key, defaultVal, title, tooltip) {
        super(key, defaultVal, title, tooltip);
    }

    getTemplate() {
        return BoolParamTemplate;
    }
}
