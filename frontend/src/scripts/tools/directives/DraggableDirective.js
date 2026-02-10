import {SvInstance} from "@/scripts/StreamVizzard";
import {Services} from "@/scripts/services/Services";

// dragStart = pointerDown (even if we don't drag after)

export default {
    bind(el, binding) {
        el.__events__ = {};
        el.__isPointerDown__ = false;

        el.__origPosClient__ = {};
        el.__currentPosEditor__ = {};
        el.__currentPosClient__ = {};

        el.setAttribute("draggable", "false");

        // Bind callback events

        if (binding.value && typeof binding.value === "object") {
            Object.keys(binding.value).forEach(eventName => {
                const handler = binding.value[eventName];
                if (typeof handler === "function") {
                    el.__events__[eventName] = handler;
                }
            });
        }

        // Bind event listener

        el.__pointerDown__ = (e) => {
            if(el.__isPointerDown__ || e.button !== 0) return; // Only left click drag

            el.__isPointerDown__ = true;

            el.__origPosClient__ = {x: e.clientX, y: e.clientY};
            el.__currentPosClient__ = {x: e.clientX, y: e.clientY};
            el.__currentPosEditor__ = {x: SvInstance.editor.mouseX, y: SvInstance.editor.mouseY};

            e.stopPropagation();

            window.addEventListener('pointermove', el.__pointerMove__);
            window.addEventListener('pointerup', el.__pointerUp__);

            if("dragStart" in el.__events__) el.__events__["dragStart"](e);
        };

        el.__pointerMove__ = (e) => {
            if(!el.__isPointerDown__) return;

            e.preventDefault();
            e.stopPropagation();

            let deltaEditor = {x: SvInstance.editor.mouseX - el.__currentPosEditor__.x,
                y: SvInstance.editor.mouseY - el.__currentPosEditor__.y};
            let deltaClient = {x: e.clientX - el.__currentPosClient__.x,
                y: e.clientY - el.__currentPosClient__.y};

            el.__currentPosEditor__ = {x: SvInstance.editor.mouseX, y: SvInstance.editor.mouseY};
            el.__currentPosClient__ = {x: e.clientX, y: e.clientY};

            if(!Services.EditorInputManager.canTranslate()) return;

            if("dragging" in el.__events__) el.__events__["dragging"](e, deltaEditor.x, deltaEditor.y, deltaClient.x, deltaClient.y); // -> Editor coordinates
        };

        el.__pointerUp__ = (e) => {
            if(!el.__isPointerDown__) return;

            el.__isPointerDown__ = false;

            let dx = el.__origPosClient__.x - e.clientX;
            let dy = el.__origPosClient__.y - e.clientY;

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

            if("dragEnd" in el.__events__) el.__events__["dragEnd"](e);
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