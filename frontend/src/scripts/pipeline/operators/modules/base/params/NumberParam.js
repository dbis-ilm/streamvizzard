import {Param} from "@/scripts/pipeline/operators/Param";
import NumberParamTemplate from "@/components/pipeline/operator/params/NumberParamTemplate.vue";

/** @typedef {import('./NumberParam.js').NumberParam} NumberParam */

export class NumberParam extends Param {

    /** @param {String} key
     * @param {Number} defaultVal
     * @param {Number} minVal
     * @param {Number} maxVal
     * @param {String} title
     * @param {String|null} tooltip **/
    constructor(key, defaultVal=0, minVal = -Number.MAX_VALUE,
                maxVal = Number.MAX_VALUE, title = "", tooltip = "",) {
        super(key, defaultVal, title, tooltip);

        this.min = minVal;
        this.max = maxVal;
    }

    getTemplate() {
        return NumberParamTemplate;
    }

    setValue(val) {
        let newVal = val;

        if(this.max != null) newVal = Math.min(this.max, newVal);
        if(this.min != null) newVal = Math.max(this.min, newVal);

        super.setValue(newVal);
    }
}