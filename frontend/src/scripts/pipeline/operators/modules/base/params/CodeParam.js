import CodeParamTemplate from "@/components/pipeline/operator/params/CodeParamTemplate.vue";
import {Param} from "@/scripts/pipeline/operators/Param";

/** @typedef {import('./CodeParam.js').CodeParam} CodeParam */

export class CodeParam extends Param {
    static CodeType = {
        UDF: "UDF",
        UDO: "UDO",
        FILTER: "FILTER"
    };

    /** @param {String} key
     * @param {CodeType} codeType
     * @param {String} defaultVal
     * @param {String} title
     * @param {String|null} tooltip **/
    constructor(key, codeType, defaultVal, title = "", tooltip = "") {
        super(key, defaultVal, title, tooltip);

        this.type = codeType;
    }

    getTemplate() {
        return CodeParamTemplate;
    }
}
