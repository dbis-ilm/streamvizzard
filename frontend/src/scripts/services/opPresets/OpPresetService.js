import {Service} from "@/scripts/services/Service";
import {Services} from "@/scripts/services/Services";
import OperatorPreset from "@/scripts/services/opPresets/OperatorPreset";
import {SvInstance} from "@/scripts/StreamVizzard";
import {v4} from "uuid";

export class OpPresetService extends Service {
    /** @type {Array<OperatorPreset>} **/ presets = [];
    /** @type {Function|null} **/ onPresetsChangeCb;

    constructor() {
        super("OpPresetService");
    }

    async fetchPresets() {
        let presets = await Services.Network.listStoredOperators();

        if(presets == null) {
            this.presets = null;

            return null;
        }

        let validPresets = [];
        for(let preset of presets) {
            let ps = new OperatorPreset().loadFromData(preset);

            if(this._fillDefinitionData(ps)) validPresets.push(ps);
        }

        this.presets = validPresets;

        if(this.onPresetsChangeCb != null) this.onPresetsChangeCb(this.presets);

        return this.presets;
    }

    /** @param {OperatorPreset} preset
     * @returns {Promise<OperatorPreset|null>} */
    async storePreset(preset) {
        let res = await Services.Network.storeOperator(preset);

        if(res) {
            this.presets = this.presets.filter(p => p.name !== preset.name);
            this.presets.unshift(preset);

            this._fillDefinitionData(preset);

            if(this.onPresetsChangeCb != null) this.onPresetsChangeCb(this.presets);

            return preset;
        }

        return null;
    }

    /** @param {String} name
     * @returns {Promise<Boolean>} */
    async deletePreset(name) {
        let res = await Services.Network.deleteStoredOperator(name);

        if(res) {
            this.presets = this.presets.filter(p => p.name !== name);

            if(this.onPresetsChangeCb != null) this.onPresetsChangeCb(this.presets);

            return true;
        }

        return false;
    }

    /** @param {OperatorPreset} preset
     * @param {Number} posX
     * @param {Number} posY */
    async createOperatorFromPreset(preset, posX, posY) {
        let createData = Object.assign({}, preset.saveData);
        createData["posX"] = posX - preset.width / 2;
        createData["posY"] = posY - preset.height / 2;
        createData["uuid"] = v4();

        let op = await SvInstance.pipeline.createOperatorFromSaveData(createData, false);

        if(op != null) op.promoteOrder(); // SaveData order might be outdated
    }

    /** @param {OperatorPreset} elm **/
    _fillDefinitionData(elm) {
        let definition = SvInstance.modules.getOperatorDefinition(elm.saveData["definition"]);
        if(definition == null) return false;

        elm.style = "background: " + definition.bgColor + "; border: var(--node-border); border-width: 1px;";

        return true;
    }
}