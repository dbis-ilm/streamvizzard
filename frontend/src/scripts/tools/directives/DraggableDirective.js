import {SvInstance} from "@/scripts/StreamVizzard";
import {Services} from "@/scripts/services/Services";

// dragStart = pointerDown (even if we don't drag after)
// allows modifiers=left,right,wheel, default=left || v-draggable.left.wheel...
// Only one drag mode can be active at a time

export default {
    bind(el, binding) {
        el.setAttribute("draggable", "false");

        let dragState = new Map();
        let currentDragState = null;

        let currentPosEditor = {};
        let currentPosClient = {};

        // Detect drag modes

        for(let mod in binding.modifiers) {
            let button = null;

            if(mod === "left") button = 0;
            else if(mod === "right") button = 2;
            else if(mod === "wheel") button = 1;
            else continue;

            dragState.set(button, { mode: mod, startPosClient: {}});
        }

        if(dragState.size === 0) dragState.set(0, { mode: "left", startPosClient: {}}); // Fallback = Left drag

        // Bind callback events

        let onDragStart = null;
        let onDragEnd = null;
        let onDrag = null;

        if (binding.value && typeof binding.value === "object") {
            Object.keys(binding.value).forEach(eventName => {
                const eventValue = binding.value[eventName];

                if (eventName === "dragStart") onDragStart = eventValue;
                else if (eventName === "dragging") onDrag = eventValue;
                else if (eventName === "dragEnd") onDragEnd = eventValue;
            });
        }

        // Bind event listener

        el.__pointerDown__ = (e) => {
            if(currentDragState != null) return; // Already a drag happening

            let dragStateEntry = dragState.get(e.button) ?? null;
            if(dragStateEntry === null) return; // Mode not supported

            currentDragState = dragStateEntry;
            currentDragState.origPosClient = {x: e.clientX, y: e.clientY};

            currentPosClient = {x: e.clientX, y: e.clientY};
            currentPosEditor = {x: SvInstance.editor.mouseX, y: SvInstance.editor.mouseY};

            e.stopPropagation();

            window.addEventListener('pointermove', el.__pointerMove__);
            window.addEventListener('pointerup', el.__pointerUp__);

            if(onDragStart != null) onDragStart(currentDragState.mode, e);
        };

        el.__pointerMove__ = (e) => {
            if(currentDragState === null) return; // No dragging active

            e.preventDefault();
            e.stopPropagation();

            let deltaEditor = {x: SvInstance.editor.mouseX - currentPosEditor.x,
                y: SvInstance.editor.mouseY - currentPosEditor.y};
            let deltaClient = {x: e.clientX - currentPosClient.x,
                y: e.clientY - currentPosClient.y};

            currentPosEditor = {x: SvInstance.editor.mouseX, y: SvInstance.editor.mouseY};
            currentPosClient = {x: e.clientX, y: e.clientY};

            if(!Services.EditorInputManager.canTranslate()) return;

            if(onDrag != null) onDrag(currentDragState.mode, e, deltaEditor.x, deltaEditor.y, deltaClient.x, deltaClient.y); // -> Editor coordinates
        };

        el.__pointerUp__ = (e) => {
            if(currentDragState == null) return; // No dragging active

            let dragStateEntry = dragState.get(e.button) ?? null;
            if(dragStateEntry !== currentDragState) return; // Mode not supported or not active

            let dx = currentDragState.startPosClient.x - e.clientX;
            let dy = currentDragState.startPosClient.y - e.clientY;

            let wasMoved = (Math.abs(dx) + Math.abs(dy)) > 1; // Pixel

            e.preventDefault();
            e.stopPropagation();

            if(wasMoved) {
                // Cancel click event which will be triggered after our pointerup
                el.addEventListener("click", (e) => {
                    e.stopImmediatePropagation();
                    e.preventDefault();
                }, {capture: true, once: true});
            }

            window.removeEventListener('pointermove', el.__pointerMove__);
            window.removeEventListener('pointerup', el.__pointerUp__);

            if(onDragEnd != null) onDragEnd(currentDragState.mode, e);

            currentDragState = null;
        };

        el.addEventListener("pointerdown", el.__pointerDown__);
    },

    unbind(el) {
        // Remove all added event listener

        window.removeEventListener('pointermove', el.__pointerMove__);
        window.removeEventListener('pointerup', el.__pointerUp__);

        el.removeEventListener("pointerdown", el.__pointerDown__);
    }
};