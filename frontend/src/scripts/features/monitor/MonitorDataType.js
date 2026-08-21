import LiteralDT from "@/components/features/monitor/displays/LiteralDT.vue";
import {safeVal, valueOr} from "@/scripts/tools/Utils";
import StringDS from "@/components/features/monitor/sidebar/settings/StringDS.vue";
import SelectDS from "@/components/features/monitor/sidebar/settings/SelectDS.vue";
import ImageDT from "@/components/features/monitor/displays/ImageDT.vue";
import ScatterplotDT from "@/components/features/monitor/displays/ScatterplotDT.vue";
import BoolDS from "@/components/features/monitor/sidebar/settings/BoolDS.vue";
import RangeDS from "@/components/features/monitor/sidebar/settings/RangeDS.vue";
import HeatmapDT from "@/components/features/monitor/displays/HeatmapDT.vue";
import NumberDS from "@/components/features/monitor/sidebar/settings/NumberDS.vue";
import TableDT from "@/components/features/monitor/displays/TableDT.vue";

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
    /** @param {Number} modeID
     * @param {String} displayName
     * @param {MonitorDisplayTemplate} template
     * @param {Object} defaults
     * @param {() => TemplateSetting[]} settingsRetriever Additional data-type specific settings to set by the user. */
    constructor(modeID, displayName, template, defaults = {}, settingsRetriever = () => []) {
        this.name = displayName;
        this.modeID = modeID;
        this.template = template;
        this.defaults = defaults;
        this.settingsRetriever = settingsRetriever;
    }

    getSafeSettings(userSettings) {
        // Collects all required setting values with default fallback
        // Keep existing settings that do not have a match here

        let set = valueOr(Object.assign({}, userSettings), {});  // Copy props

        // First take template-defined props as baseline (some are not available as setting options)
        for (let key in this.defaults) set[key] = this.defaults[key];

        // Now override props based on setting options and userProps
        for(let op of this.getSettingsOptions(userSettings)) set[op.key] = op.value;

        return set;
    }

    /** @param {Object} userProps
     * @returns {TemplateSetting[]} */
    getSettingsOptions(userProps) {
        let safeUserProps = valueOr(userProps, {});
        let settings = this.template.getSettings(safeUserProps, this.defaults);

        for(let add of this.settingsRetriever()) {
            add.value = safeVal(safeUserProps[add.key], add.def);
            settings.push(add);
        }

        return settings;
    }
}

export class TemplateSetting {
    /** @param {String} key
     * @param {String} name
     * @param {Object} value
     * @param {Object} def
     * @param {Object} template
     * @param {String} desc
     * @param {Object|null} data **/
    constructor(key, name, value, def, template, desc, data = null) {
        this.key = key;
        this.name = name;
        this.value = value;
        this.def = def;
        this.template = template;
        this.desc = desc;
        this.data = data;
    }
}

class MonitorDisplayTemplate {
    /** @param {Object}  component
     * @param {(props: Object, propsDef: Object) => TemplateSetting[]} settingsRetriever
     * @param {Boolean} syncProps */
    constructor(component, settingsRetriever, syncProps=false) {
        this.component = component;
        this._settingsRetriever = settingsRetriever;
        this.syncProps = syncProps; // True, if the user props should be sent to the backend (for preparing visualized data)
    }

    /** @returns {TemplateSetting[]} */
    getSettings(userProps, defaultProps) {
        return this._settingsRetriever(userProps, defaultProps);
    }
}

export const DT_Literal = new MonitorDisplayTemplate(LiteralDT, (props, propsDef) => {
    let expDef = safeVal(propsDef.exp, "$VAL");
    let exp = safeVal(props.exp, expDef);

    let maxLengthDef = safeVal(propsDef.maxLength, "1000");
    let maxLength = safeVal(props.maxLength, maxLengthDef);

    let styleDef = safeVal(propsDef.style, null);
    let style = safeVal(props.style, styleDef);

    let alignDef = safeVal(propsDef.align, "Center");
    let align = safeVal(props.align, alignDef);

    return [new TemplateSetting("exp", "Expression", exp, expDef, StringDS, "How to display the value. $VAL signals the value to display. JS code can be used but needs to return a string.\nExample: \"Value: \" + $VAL.toUpperCase()"),
            new TemplateSetting("maxLength", "Max Length", maxLength, maxLengthDef, StringDS, "How many characters the display string will have at most"),
            new TemplateSetting("style", "Style", style, styleDef, StringDS, "Css style of the display text. Separate multiple values with ';'\nExample: font-weight:bold; font-size:24px;"),
            new TemplateSetting("align", "Alignment", align, alignDef, SelectDS, "Alignment of the display text", ["Center", "Left", "Right"])
    ]
});

export const DT_Table = new MonitorDisplayTemplate(TableDT, () => { return []; }, true);

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

    let xRangeDef = safeVal(propsDef.xrange, [null, null]);
    let xRange = safeVal(props.xrange, xRangeDef);

    let yRangeDef = safeVal(propsDef.yrange, [null, null]);
    let yRange = safeVal(props.yrange, yRangeDef);

    let maxBufferDef = safeVal(propsDef.maxBufferElements, 100);
    let maxBuffer = safeVal(props.maxBufferElements, maxBufferDef);

    return [new TemplateSetting("xvisible", "Show X Axis", xVis, xVisDef, BoolDS, "Displays the x axis"),
            new TemplateSetting("yvisible", "Show Y Axis", yVis, yVisDef, BoolDS, "Displays the y axis"),
            new TemplateSetting("xtitle", "X Title", xTitle, xTitleDef, StringDS, "The title of the x axis"),
            new TemplateSetting("ytitle", "Y Title", yTitle, yTitleDef, StringDS, "The title of the y axis"),
            new TemplateSetting("xrange", "X Range", xRange, xRangeDef, RangeDS, "The data range of the x axis. Either both sides or none can be set."),
            new TemplateSetting("yrange", "Y Range", yRange, yRangeDef, RangeDS, "The data range of the y axis. Either both sides or none can be set."),
            new TemplateSetting("maxBufferElements", "Max. Points", maxBuffer, maxBufferDef, NumberDS, "How many data points to display at max per plot (sampled otherwise)")
    ];
}, true);

export const DT_Heatmap = new MonitorDisplayTemplate(HeatmapDT, (props, propsDef) => {
    let xTitleDef = safeVal(propsDef.xtitle, null);
    let xTitle = safeVal(props.xtitle, xTitleDef);

    let yTitleDef = safeVal(propsDef.ytitle, null);
    let yTitle = safeVal(props.ytitle, yTitleDef);

    let zTitleDef = safeVal(propsDef.ztitle, null);
    let zTitle = safeVal(props.ztitle, zTitleDef);

    let yRangeDef = safeVal(propsDef.yrange, [null, null]);
    let yRange = safeVal(props.yrange, yRangeDef);

    let maxCellsDef = safeVal(propsDef.maxCells, 1000);
    let maxCells = safeVal(props.maxCells, maxCellsDef);

    return [
        new TemplateSetting("xtitle", "X Title", xTitle, xTitleDef, StringDS, "The title of the x axis"),
        new TemplateSetting("ytitle", "Y Title", yTitle, yTitleDef, StringDS, "The title of the y axis"),
        new TemplateSetting("ztitle", "Z Title", zTitle, zTitleDef, StringDS, "The title of the z axis (color)"),
        new TemplateSetting("yrange", "Y Range", yRange, yRangeDef, RangeDS, "The data range of the y axis. Either both sides or none can be set."),
        new TemplateSetting("maxCells", "Max. Cells", maxCells, maxCellsDef, NumberDS, "How many data cells to display at max (sampled otherwise)")
    ];
}, true);