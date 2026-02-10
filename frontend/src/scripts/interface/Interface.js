import {safeVal} from "@/scripts/tools/Utils";
import {EVENTS, executeEvent} from "@/scripts/tools/EventHandler";

export default class Interface {
    constructor() {
        /** @type {Object<String, Modal>} **/
        this.modals = {};

        this.showSidebar = true;
        this.showOpPresetBar = false;
    }

    // ----------------------------------------------------- Modals ----------------------------------------------------

    /** @param {Modal} modal **/
    registerModal(modal) {
        this.modals[modal.name] = modal;
    }

    /** @param {String} name
     * @param {Object} params **/
    openModal(name, params= []) {
        let modal = this.modals[name] || null;
        if(modal == null) return;

        if(!Array.isArray(params)) params = [params];

        this.closeAllModals(); // Close all previous modals

        executeEvent(EVENTS.MODAL_OPENED, name);

        modal.openFunc(...params);
    }

    /** @param {String} name **/
    closeModal(name) {
        let modal = this.modals[name] || null;
        if(modal == null) return;

        modal.closeFunc();
    }

    closeAllModals() {
        for(let modal of Object.values(this.modals)) this.closeModal(modal.name);
    }

    // ----------------------------------------------------- Storage ---------------------------------------------------

    exportSaveData() {
        return {
            "showSidebar": this.showSidebar,
            "showOpPresetBar": this.showOpPresetBar
        }
    }

    importSaveData(data) {
        this.showSidebar = safeVal(data["showSidebar"], this.showSidebar);
        this.showOpPresetBar = safeVal(data["showOpPresetBar"], this.showOpPresetBar);
    }
}

export class Modal {
    /** @param String **/ name
    /** @param Function **/ openFunc
    /** @param Function **/ closeFunc
    constructor(name, openFunc, closeFunc) {
        this.name = name;
        this.openFunc = openFunc;
        this.closeFunc = closeFunc;
    }
}

export const MODALS = {
    OP_PRESET_STORE: "OP_PRESET_STORE",
    OP_PRESET_EDIT: "OP_PRESET_EDIT",
    STORE_PIPELINE: "STORE_PIPELINE",
    SIMULATE_PIPELINE: "SIMULATE_PIPELINE",
}
