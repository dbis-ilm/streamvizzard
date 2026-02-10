import $ from "jquery"

import {Service} from "@/scripts/services/Service";

// Listens for interaction with editor inputs and prevents zooming/translation of the underlying editor

export class EditorInputManageService extends Service {
    constructor() {
        super("EditorInputManager");

        this.selectedHtmlElm = null;
    }

    onInitialize() {
        super.onInitialize();

        $(document).on('focusin focus', '.editorInput', (e) => {
            this.onInputSelected(e.currentTarget);
        });

        $(document).on('focusout blur', '.editorInput', (e) => {
            this.onInputDeselected(e.currentTarget);
        });

        $(document).on('keydown', '.editorInput', (e) => {
            if(e.key === 'Escape' || e.key === "Enter") this.onInputDeselected(e.currentTarget);
        });
    }

    // -----------------------------------------------------------------------------------------------------------------

    // Force blurring/focusing. Make sure, element is an editorInput. Sometimes we call with dummy elements to block translation!

    _isValidEditorInput() {
        if(this.selectedHtmlElm == null || !(this.selectedHtmlElm instanceof HTMLElement)) return false;

        return this.selectedHtmlElm.classList.contains("editorInput");
    }

    _isActive() {
        return this.selectedHtmlElm.hasAttribute("ei-active");
    }

    _blurCurrentTarget() {
        // Manually blurs the editorInput field

        let elm = this.selectedHtmlElm;

        elm.dispatchEvent(new Event('deactivate'));
        elm.blur(); // Triggers blur listener
    }

    // -----------------------------------------------------------------------------------------------------------------

    onInputSelected(htmlElm) {
        if(this._isValidEditorInput() && this.selectedHtmlElm !== htmlElm) this._blurCurrentTarget();

        this.selectedHtmlElm = htmlElm;

        if(this._isValidEditorInput() && !this._isActive()) {
            this.selectedHtmlElm.setAttribute("ei-active", true); // Classes do not stick on reactive vue comps
        }
    }

    onInputDeselected(htmlElm=null) {
        // Only deselect current elm (force if null)
        if((htmlElm != null && htmlElm !== this.selectedHtmlElm) || this.selectedHtmlElm == null) return;

        if(this._isValidEditorInput() && this._isActive()) {
            this.selectedHtmlElm.removeAttribute("ei-active");

            this._blurCurrentTarget();
        }

        this.selectedHtmlElm = null;
    }

    hasSelectedInput() {
        return this.selectedHtmlElm != null;
    }

    isElementSelected(element) {
        return this.selectedHtmlElm === element;
    }

    canTranslate() {
        return !this.hasSelectedInput();
    }

    canZoom() {
        return !this.hasSelectedInput();
    }
}
