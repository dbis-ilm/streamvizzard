import {getComponents} from "@/scripts/pipeline/operators/modules/index";

export class Modules {
    constructor() {
        /** @type {Array<Definition>} **/
        this.opDefinitions = [];

        /** @type {Map<String, Definition>} **/
        this._defLookup = new Map();
    }

    load() {
        this.opDefinitions = getComponents();

        for (let def of this.opDefinitions) this._defLookup.set(def.getFullPath(), def);
    }

    /** @return {Definition|null} **/
    getOperatorDefinition(path) {
        return this._defLookup.get(path);
    }
}