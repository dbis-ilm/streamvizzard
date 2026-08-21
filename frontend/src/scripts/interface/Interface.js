import {safeVal} from "@/scripts/tools/Utils";
import {EVENTS, executeEvent} from "@/scripts/tools/EventHandler";
import Vue from "vue";

export default class Interface {
    constructor() {
        /** @type {Object<String, Modal>} **/
        this.modals = {};

        this.showSidebar = true;
        this.showOpPresetBar = false;

        this.sidebarViewRect = new ViewRect();
        this.opPresetBarViewRect = new ViewRect();
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

    async importSaveData(data) {
        this.showSidebar = safeVal(data["showSidebar"], this.showSidebar);
        this.showOpPresetBar = safeVal(data["showOpPresetBar"], this.showOpPresetBar);

        // Await reactiveness and add some timeout to ensure that sidebars are in correct state before continue
        await Vue.nextTick();
        await new Promise(r => setTimeout(r, 10)); // Force macro task wait to repaint DOM
    }
}

export class ViewRect {
    /** @param {number} left
     * @param {number} top
     * @param {number} width
     * @param {number} height */
    constructor(left = 0, top = 0, width = 0, height = 0) {
        this.left = left;
        this.top = top;
        this.width = width;
        this.height = height;
    }

    get right() {
        return this.left + this.width
    }

    get bottom() {
        return this.top + this.height
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
