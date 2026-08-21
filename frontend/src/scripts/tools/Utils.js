import Vue from "vue";

export function formatTime ( seconds, minVal = 0.01, minBreakPoint = 300) {
    let sAbs = Math.abs(seconds);

    if(seconds === 0 || minVal != null && sAbs <= minVal) return "0s";

    if(sAbs >= minBreakPoint) return parseFloat((seconds / 60).toFixed(2)) + "min";
    else if(sAbs >= 0.1) return parseFloat(seconds.toFixed(2)) + "s";
    else return parseFloat((seconds * 1000).toFixed(2)) + "ms";
}

export function formatDataSize(dataSize, minBreakPoint = 2000) {
    // DataSize Input in MB

    let sAbs = Math.abs(dataSize);

    if(sAbs >= minBreakPoint) return parseFloat((dataSize / 1000).toFixed(2)) + "GB";
    else if(sAbs >= 0.1) return parseFloat(dataSize.toFixed(2)) + "MB";
    else return parseFloat((dataSize * 1000).toFixed(2)) + "KB";
}

export function distance(x1, y1, x2, y2) {
    return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
}

export function remap(val, from1, to1, from2, to2, clamped=false) {
    if(clamped) {
        val = clamp(val, from1, to1);
    }

    return ((val - from1) / (to1 - from1)) * (to2 - from2) + from2;
}

export function clamp(val, min, max) {
    return Math.min(Math.max(val, min), max);
}

export function debounce(fn, delay) {
    let t;
    let pending = false;

    function wrapper(...args) {
        pending = true;

        clearTimeout(t);
        t = setTimeout(() => {
            pending = false;
            fn.apply(this, args);
        }, delay);
    }

    wrapper.isPending = () => pending;

    wrapper.cancel = () => {
        if(pending) {
            clearTimeout(t);
            pending = false;
        }
    };

    return wrapper;
}

export function makeGenericResizable(jqElement, onResize = null, autoHide = false, handles = null) {
    Vue.nextTick(function() {
        jqElement.resizable({
            autoHide: autoHide,
            handles: handles,
            resize(event, ui) {
                if(onResize != null) onResize(ui.size);
            }
        });

        // Add handle icons because jquery only provides the SE icon
        jqElement.find('.ui-resizable-ne').addClass('resizableHandleNE ui-icon ui-icon-gripsmall-diagonal-se');
        jqElement.find('.ui-resizable-nw').addClass('resizableHandleNW ui-icon ui-icon-gripsmall-diagonal-se');
    });
}

export function makeNameInput(jqElement, triggerElement) {
    //A name input is activated by two clicks on the trigger element
    //Dragging is not allowed and will not trigger the input

    //Initial
    jqElement.removeClass("enabled");
    jqElement.css("pointer-events", "none");

    triggerElement.prop("data-cc", 0);
    triggerElement.prop("data-md", 0);

    // Avoid triggering "click" while dragging element
    triggerElement.on("mousedown", function(e) {
        // Skip if we already selected input (allow double click to select text)
        if(triggerElement.prop("data-cc") === 2 && e.detail >= 2) return;

        triggerElement.prop("data-md", 0);
    });
    triggerElement.on("mousemove", function() {
        triggerElement.prop("data-md", 1);
    });

    //Active input
    triggerElement.on("click", function(e) {
        if(triggerElement.prop("data-md") === 1) return; //We dragged the element, no click
        if(triggerElement.prop("data-cc") === 0) { //Single Click, we only trigger at two clicks
            triggerElement.prop("data-cc", 1);

            return;
        }

        if(triggerElement.prop("data-cc") === 2) return; // Do not trigger enable twice

        triggerElement.prop("data-cc", 2);

        jqElement.addClass("enabled");
        jqElement.css("pointer-events", "all");
        jqElement.get(0).setSelectionRange(-1, -1); // Set cursor to end (also resets text selection)
        jqElement.focus();

        e.stopPropagation();
        e.preventDefault();
    });

    //Remove click counter on leave
    triggerElement.on("mouseout", function() {
        if(triggerElement.prop("data-cc") !== 2) triggerElement.prop("data-cc", 0);
    });

    //End input with enter key
    jqElement.on("keyup", function(e) {
        if (e.key === 'Enter' || e.keyCode === 13) {
            jqElement.removeClass("enabled");
            jqElement.css("pointer-events", "none");
            jqElement.blur();

            e.preventDefault();
        }
    });

    // Forbid line-break value inside input/textarea
    jqElement.on("keydown", function(e) {
        if (e.key === 'Enter' || e.keyCode === 13) {
            e.preventDefault();
        }
    });

    //End input by deselect
    jqElement.on("focusout", function() {
        jqElement.removeClass("enabled");
        jqElement.css("pointer-events", "none");
        triggerElement.prop("data-cc", 0);
    });
}

/** @param {any} val
 * @param {any|null} def **/
export function safeVal(val, def=null) {
    return val !== undefined ? val : def;
}

/** @param {any} val
 * @param {any|null} def **/
export function valueOr(val, def=null) {
    return safeVal(val) != null ? val : def;
}

/** @param {Array<SvOperator>} ops
 * @param {Number} margin **/
export function getOperatorBoundingBox(ops, margin = 0) {
    let left = Math.min(...ops.map(op => op.posX)) - margin;
    let top = Math.min(...ops.map(op => op.posY)) - 2 * margin;
    let right = Math.max(...ops.map(op => op.posX + op.width)) + margin;
    let bottom = Math.max(...ops.map(op => op.posY + op.height)) + margin;

    if(ops.length === 0) {
        left = 0;
        top = 0;
        right = 0;
        bottom = 0;
    }

    return { left, right, top, bottom,
        width: Math.abs(left - right),
        height: Math.abs(top - bottom),
        centerX: (left + right) / 2,
        centerY: (top + bottom) / 2,
    };
}

/** Checks if two bounding boxes overlap
 * @param {number} left1
 * @param {number} top1
 * @param {number} right1
 * @param {number} bottom1
 * @param {number} left2
 * @param {number} top2
 * @param {number} right2
 * @param {number} bottom2 **/
export function intersects(left1, top1, right1, bottom1, left2, top2, right2, bottom2) {
    return !(
        left1 > right2 ||
        right1 < left2 ||
        top1 > bottom2 ||
        bottom1 < top2
    );
}

/** @param {number} left
 * @param {number} top
 * @param {number} right
 * @param {number} bottom
 * @param {Number} x
 * @param {Number} y */
export function containsPoint(left, top, right, bottom, x, y) {
    return (
        x >= left &&
        x <= right &&
        y >= top &&
        y <= bottom
    );
}
