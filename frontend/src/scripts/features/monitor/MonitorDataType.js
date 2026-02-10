import LiteralDT from "@/components/features/monitor/displays/LiteralDT.vue";
import {safeVal, valueOr} from "@/scripts/tools/Utils";
import StringDS from "@/components/features/monitor/sidebar/settings/StringDS.vue";
import SelectDS from "@/components/features/monitor/sidebar/settings/SelectDS.vue";
import ImageDT from "@/components/features/monitor/displays/ImageDT.vue";
import ScatterplotDT from "@/components/features/monitor/displays/ScatterplotDT.vue";
import BoolDS from "@/components/features/monitor/sidebar/settings/BoolDS.vue";
import RangeDS from "@/components/features/monitor/sidebar/settings/RangeDS.vue";

export class MonitorDataType {
    constructor(name, displayName) {
        this.name = name;
        this.displayName = displayName;

        /** @type {Map<int, MonitorDisplayMode>} **/
        this.displayModes = new Map();
    }

    registerDisplayMode(displayMode) {
        this.displayModes.set(displayMode.modeID, displayMode);
    }

    /** @type MonitorDisplayMode **/
    getDisplayMode(modeID, fallbackDefault=true) {
        return this.displayModes.get(modeID) || (fallbackDefault ? this.getDefaultMode() : null);
    }

    /** @type MonitorDisplayMode **/
    getDefaultMode() {
        if(this.displayModes.size === 0) return null;

        return this.displayModes.values().next().value; // First value
    }

    getAllDisplayModes() {
        return this.displayModes;
    }
}

export class MonitorDisplayMode {
    constructor(modeID, name, template, props = {}) {
        this.name = name;
        this.modeID = modeID;
        this.template = template;
        this.props = props;
    }

    getSafeSettings(userSettings) {
        // Collects all required setting values with default fallback
        // Keep existing settings that do not have a match here

        let set = valueOr(Object.assign({}, userSettings), {});  // Copy props

        // First take template-defined props as baseline (some are not available as setting options)
        for (let key in this.props) set[key] = this.props[key];

        // Now override props based on setting options and userProps
        for(let op of this.getSettingsOptions(userSettings)) set[op.key] = op.value;

        return set;
    }

    getSettingsOptions(userProps) {
        return this.template.getSettings(valueOr(userProps, {}), this.props);
    }
}

class MonitorDisplayTemplate {
    constructor(component, settingsRetriever, syncProps=false) {
        this.component = component;
        this._settingsRetriever = settingsRetriever;
        this.syncProps = syncProps; // True, if the user props should be sent to the backend (for preparing visualized data)
    }

    getSettings(userProps, defaultProps) {
        return this._settingsRetriever(userProps, defaultProps);
    }
}

export const DT_Literal = new MonitorDisplayTemplate(LiteralDT, (props, propsDef) => {
    let expDef = safeVal(propsDef.exp, "$VAL");
    let exp = safeVal(props.exp, expDef);

    let maxLengthDef = safeVal(propsDef.maxLength, null);
    let maxLength = safeVal(props.maxLength, maxLengthDef);

    let styleDef = safeVal(propsDef.style, null);
    let style = safeVal(props.style, styleDef);

    let alignDef = safeVal(propsDef.align, "Center");
    let align = safeVal(props.align, alignDef);

    return [{"key": "exp", "name": "Expression", "value": exp, "desc": "How to display the value. $VAL signals the value to display. " +
            "JS code can be used but needs to return a string.\nExample: \"Value: \" + $VAL.toUpperCase()", "default": expDef, "template": StringDS},
            {"key": "maxLength", "name": "Max Length", "value": maxLength, "desc": "How many characters the display string will have at most", "default": maxLengthDef, "template": StringDS},
            {"key": "style", "name": "Style", "value": style, "desc": "Css style of the display text. Separate multiple values with ';'\nExample: font-weight:bold; font-size:24px;", "default": styleDef, "template": StringDS},
            {"key": "align", "name": "Alignment", "value": align, "data": ["Center", "Left", "Right"], "desc": "Alignment of the display text", "default": alignDef, "template": SelectDS}]}
);

export const DT_Image = new MonitorDisplayTemplate(ImageDT, () => { return []; }, true);

export const DT_Scatterplot = new MonitorDisplayTemplate(ScatterplotDT, (props, propsDef) => {
    let xVisDef = safeVal(propsDef.xvisible, true);
    let xVis = safeVal(props.xvisible, xVisDef);

    let yVisDef = safeVal(propsDef.yvisible, true);
    let yVis = safeVal(props.yvisible, yVisDef);

    let xTitleDef = safeVal(propsDef.xtitle, null);
    let xTitle = safeVal(props.xtitle, xTitleDef);

    let yTitleDef = safeVal(propsDef.ytitle, null);
    let yTitle = safeVal(props.ytitle, yTitleDef);

    let xRangeDef = safeVal(propsDef.xrange, null);
    let xRange = safeVal(props.xrange, xRangeDef);

    let yRangeDef = safeVal(propsDef.yrange, null);
    let yRange = safeVal(props.yrange, yRangeDef);

    let maxBufferDef = safeVal(propsDef.maxBufferElements, null);
    let maxBuffer = safeVal(props.maxBufferElements, maxBufferDef);

    return [{"key": "xvisible", "name": "Show X Axis", "value": xVis, "desc": "Displays the x axis", "default": xVisDef, "template": BoolDS},
        {"key": "yvisible", "name": "Show Y Axis", "value": yVis, "desc": "Displays the y axis", "default": yVisDef, "template": BoolDS},
        {"key": "xtitle", "name": "X Title", "value": xTitle, "desc": "The title of the x axis", "default": xTitleDef, "template": StringDS},
        {"key": "ytitle", "name": "Y Title", "value": yTitle, "desc": "The title of the y axis", "default": yTitleDef, "template": StringDS},
        {"key": "xrange", "name": "X Range", "value": xRange, "desc": "The data range of the x axis", "default": xRangeDef, "template": RangeDS},
        {"key": "yrange", "name": "Y Range", "value": yRange, "desc": "The data range of the y axis", "default": yRangeDef, "template": RangeDS},
        {"key": "maxBufferElements", "name": "Max. Points", "value": maxBuffer, "desc": "How many data points to display at max per plot (sample otherwise)", "default": maxBufferDef, "template": StringDS}];
});