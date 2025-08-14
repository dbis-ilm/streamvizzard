import $ from "jquery";
import Vue from "vue";
import {system} from "@/main";
import Rete from "rete";

export async function sleep(seconds) {
    await new Promise((resolve) => {
        setTimeout(() => resolve("done"), seconds * 1000)
    });
}

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

export function calcHeatmapColor(gradientValue) {
    gradientValue = clamp(gradientValue, 0, 1);

    const sliderWidth = 1

    const gradient = [
        [
            0,
            [100, 200, 255]
        ],
        [
            0.33,
            [255, 255, 100]
        ],
        [
            0.66,
            [255, 100, 100]
        ],
        [
            1,
            [255, 100, 255]
        ]
    ];

    if(gradientValue === 0) return 'rgb(' + gradient[0][1][0] + ',' + gradient[0][1][1] + ',' + gradient[0][1][2] + ')';
    else if(gradientValue === 1) return 'rgb(' + gradient[gradient.length - 1][1][0] + ',' + gradient[gradient.length - 1][1][1] + ',' + gradient[gradient.length - 1][1][2] + ')';

    let colorRange = []
    $.each(gradient, function( index, value ) {
        if(gradientValue<=value[0]) {
            colorRange = [Math.max(0, index-1),index]
            return false;
        }
    });

    //Get the two closest colors
    let firstcolor = gradient[colorRange[0]][1];
    let secondcolor = gradient[colorRange[1]][1];

    //Calculate ratio between the two closest colors
    let firstcolor_x = sliderWidth*(gradient[colorRange[0]][0]);
    let secondcolor_x = sliderWidth*(gradient[colorRange[1]][0])-firstcolor_x;
    let slider_x = sliderWidth*(gradientValue)-firstcolor_x;
    let ratio = slider_x/secondcolor_x;

    //Get the color with pickHex(thx, less.js's mix function!)
    let result = pickHex( secondcolor,firstcolor, ratio );

    return 'rgb(' + result[0] + ',' + result[1] + ',' + result[2] + ')';
}

function pickHex(color1, color2, weight) {
    let w = weight * 2 - 1;
    let w1 = (w/1+1) / 2;
    let w2 = 1 - w1;
    return [Math.round(color1[0] * w1 + color2[0] * w2),
        Math.round(color1[1] * w1 + color2[1] * w2),
        Math.round(color1[2] * w1 + color2[2] * w2)];
}

export function distance(x1, y1, x2, y2) {
    return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
}

export function remap(val, from1, to1, from2, to2) {
    return ((val - from1) / (to1 - from1)) * (to2 - from2) + from2;
}

export function clamp(val, min, max) {
    return Math.min(Math.max(val, min), max);
}

export function makeResizable(jqElement, node, key, autoHide = false) {
    Vue.nextTick(function() {
        jqElement.parent().addClass("resizableCtrl"); //In case of dynamically created elements

        node.vueContext.registerResizable(jqElement, key);

        jqElement.resizable({
            autoHide: autoHide,
            start: function() {
                node.isResized = true;
            },
            stop: function() {
                node.isResized = false;
            },
            resize(event, ui) {
                node.vueContext.onElementResize(key, ui.size);

                node.component.updateVisuals(node);
            }
        });
    });
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

export function applyResize(jqElement, settings) {
    if(settings.width !== undefined) jqElement.width(settings.width);
    if(settings.height !== undefined) jqElement.height(settings.height);
}

export function makeNameInput(jqElement, triggerElement, disabledCssClass) {
    //A name input is activated by two clicks on the trigger element
    //Dragging is not allowed and will not trigger the input

    //Initial
    if(disabledCssClass != null) jqElement.addClass(disabledCssClass);
    jqElement.css("pointer-events", "none");

    triggerElement.prop("data-cc", 0);
    triggerElement.prop("data-md", 0);

    // Avoid triggering "click" while dragging element
    triggerElement.on("mousedown", function() {
        triggerElement.prop("data-md", 0);
    });
    triggerElement.on("mousemove", function() {
        triggerElement.prop("data-md", 1);
    });

    //Active input
    triggerElement.on("click", function() {
        if(triggerElement.prop("data-md") === 1) return; //We dragged the element, no click
        if(triggerElement.prop("data-cc") === 0) { //Single Click, we only trigger at two clicks
            triggerElement.prop("data-cc", 1);

            return;
        }

        triggerElement.prop("data-cc", 0);

        if(disabledCssClass != null) jqElement.removeClass(disabledCssClass);
        jqElement.css("pointer-events", "all");
        jqElement.css("text-decoration", "underline");
        jqElement.focus();
    });

    //Remove click counter on leave
    triggerElement.on("mouseout", function() {
        triggerElement.prop("data-cc", 0);
    });

    //End input with enter key
    jqElement.on("keyup", function(e) {
        if (e.key === 'Enter' || e.keyCode === 13) {
            if(disabledCssClass != null) jqElement.addClass(disabledCssClass);
            jqElement.css("pointer-events", "none");
            jqElement.css("text-decoration", "none");
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
        if(disabledCssClass != null) jqElement.addClass(disabledCssClass);
        jqElement.css("pointer-events", "none");
        jqElement.css("text-decoration", "none");
    });
}

export function safeVal(val, def=null) {
    return val !== undefined ? val : def;
}

export function valueOr(val, def=null) {
    return safeVal(val) != null ? val : def;
}

export function registerAutoBorderSize(element, defaultSize, onZoom= null) {
    let refZoom = 1;

    // TODO: Optimize border width / radius calculation to avoid pixelation
    system.editor.on('editorZoom', function(data) {
        // Don't rely on the default zoom event since this might be canceled
        let zoomAmount = data.zoom;
        let zoomFac = refZoom / zoomAmount;

        // Add a little offset to fight aliasing and pixel rounding errors
        let bonusOffset = (zoomAmount < 1 ? 1 : 0) * (remap(clamp(zoomAmount, 0.5, 1), 0.5, 1, 1, 0));

        element.style.borderWidth = Math.max(defaultSize, (zoomFac * defaultSize) + bonusOffset) + "px";

        // Resize observer might not detect changes in border if content-box is set

        if(onZoom != null) onZoom(zoomFac);
    });

    //Initial
    let zoomFac = refZoom / system.editor.view.area.transform.k;

    element.style.borderWidth = Math.max(defaultSize, (zoomFac * defaultSize)) + "px";

    if(onZoom != null) onZoom(zoomFac);
}

export async function createNode(component, { id = null, x = 0, y = 0 }) {
    const node = new Rete.Node(component.name);
    if(id != null) node.id = id;
    node.position[0] = x;
    node.position[1] = y;

    await component.builder(node);

    return node;
}

export function createConnection(editor, output, input, id=null) {
    //Override connect to set id before calling the events
    if (!editor.trigger('connectioncreate', { output, input })) return;

    try {
        const connection = output.connectTo(input);

        if(id != null) connection.id = id;
        editor.view.addConnection(connection);

        editor.trigger('connectioncreated', connection);
    } catch (e) {
        editor.trigger('warn', e);
    }
}