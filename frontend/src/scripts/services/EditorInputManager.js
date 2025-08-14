import $ from "jquery"
import {Service} from "@/scripts/services/Services";

// Listens for interaction with editor inputs and prevents zooming/translation of the underlying editor

class _EditorInputManager extends Service {
    constructor() {
        super("EditorInputManager");

        this.selectedHtmlElm = null;

        //@focusin="onSelected" @focusout="onDeselected" @pointermove.stop="" @wheel.stop=""

        let ths = this;

        $(document).on('focusin', '.editorInput', function(e) {
            ths.onInputSelected(e.currentTarget);
        });

        $(document).on('focusout', '.editorInput', function(e) {
            ths.onInputDeselected(e.currentTarget);
        });

        $(document).on('keydown', '.editorInput', function(e) {
            if(e.key === 'Escape') e.currentTarget.blur();
        });

        $(document).on('pointerdown', '.editorInput', function(e) {
            e.stopPropagation(); // Prevent drag of node when selecting element
        });
    }

    onInputSelected(htmlElm) {
        if(this.selectedHtmlElm != null) this.selectedHtmlElm.blur();

        this.selectedHtmlElm = htmlElm;
    }

    onInputDeselected() {
        this.selectedHtmlElm = null;
    }

    hasSelectedInput() {
        return this.selectedHtmlElm != null;
    }

    isElementSelected(element) {
        return this.selectedHtmlElm === element;
    }
}

export const EditorInputManager = new _EditorInputManager();
