import {PipelineService} from "@/scripts/services/pipelineState/PipelineService";

function getOtherClusterSideCompileOp(nodeID, conID) {
    let con = PipelineService.getConnectionByID(conID);

    return con.input.node.id === nodeID ? con.output.node : con.input.node;
}

export function matchOtherClusterSideParams(nodeID, conID, paramKey, paramValue) {
    // Fetches operator of other side of the connection and sets matching
    // params of his selected connector to our changed value.

    let otherClusterOp = getOtherClusterSideCompileOp(nodeID, conID);

    if(otherClusterOp == null) return;

    let otherClusterCD = otherClusterOp.compileData;

    if(otherClusterCD == null) return;

    // Gets the config for the connector of the current connection
    let otherCon = otherClusterCD.config?.cluster?.["ccs"][conID]

    if(otherCon == null) return;

    // Adapt params, only consider params of his selected connector - full path for safe store into node data

    otherClusterOp.compileData.config.cluster["ccs"][conID]["params"] = matchParams({[paramKey]: paramValue}, otherCon["params"]);
}

export function matchOtherClusterSideConType(nodeID, conID, conType, conParams) {
    // Adapt other side of the cluster to select a matching connector to ours [if possible]

    let otherClusterOp = getOtherClusterSideCompileOp(nodeID, conID);

    if(otherClusterOp == null) return false;

    let otherClusterCD = otherClusterOp.compileData;

    if(otherClusterCD == null) return false;

    let otherClusterOptions = otherClusterCD["clusterConnections"][conID] ?? null

    // Gets the config for the connector of the current connection
    let otherClusterCfg = otherClusterCD.config?.cluster?.["ccs"][conID]

    if(otherClusterCfg == null || otherClusterOptions == null) return false;

    // Choose connector that has our value for "otherConType"

    for(let option of otherClusterOptions) {
        if(option["otherConType"] === conType) {
            otherClusterCfg["conType"] = option["ourConType"];
            otherClusterCfg["params"] = {...option["ourConParams"]};

            // Match other keys with ours - full path for safe store into node data

            otherClusterOp.compileData.config.cluster["ccs"][conID]["params"] = matchParams(conParams, otherClusterCfg["params"]);

            return true;
        }
    }

    return false;
}

function matchParams(ourParams, otherParams) {
    for(let [paramKey, paramValue] of Object.entries(ourParams)) {
        for(let ok of Object.keys(otherParams)) {
            if(ok === paramKey) otherParams[ok] = paramValue;
        }
    }

    return otherParams;
}

// --- Compile Option  Select---

class CompileOptionBase {
    constructor(type, key, title, tooltip, defaultValue) {
        this.id = key;
        this.key = key;
        this.title = title;
        this.tooltip = tooltip;
        this.defaultValue = defaultValue;
        this.value = defaultValue;

        this.type = type;
        this.show = true;

        this.strategy = null;

        this.skipOnExport = false;
    }

    onLoad() {}

    onValueChange(newVal) {
        this.setValue(newVal);

        this.strategy.onElmValueChanged(this);
    }

    setValue(newVal) {
        this.value = newVal;
    }

    getValue() {
        return this.value;
    }
}

class CompileOptionBaseHelper extends CompileOptionBase {
    constructor(type) {
        super(type);

        this.skipOnExport = true;
    }

    onValueChange() {}
}

export class CompileOptionGrouper extends CompileOptionBaseHelper {
    constructor(title, tooltip, elements) {
        super("Grouper");

        this.tooltip = tooltip;
        this.title = title;

        this.elements = elements;

        this.open = true;
    }

    onToggle() {
        for(let elm of this.elements) elm.show = this.open;
    }
}

export class CompileOptionSlider extends CompileOptionBase {
    constructor(key, title, tooltip, defaultValue, sliderGroup = null) {
        super("Slider", key, title, tooltip, defaultValue);

        this.sliderGroup = sliderGroup;

        if(this.sliderGroup != null) this.sliderGroup.registerSlider(this);
    }

    onValueChange(newVal) {
        super.onValueChange(newVal);

        if(this.sliderGroup != null) this.sliderGroup.normalizeSlider(this);
    }
}

export class CompileOptionSliderGroup {
    constructor() {
        this.slider = [];
    }

    registerSlider(slider) {
        this.slider.push(slider);
    }

    onLoad() {
        this.normalizeSlider();
    }

    hasSlider() {
        return this.slider.length > 0;
    }

    normalizeSlider(slider=null) {
        if(!this.hasSlider() || this.slider.length < 2) return;

        if(slider == null) slider = this.slider[0];

        // Limit the total slider values to 1 by keeping the value of the current slider

        let remainingTotal = Math.max(0, 1 - slider.value);
        let sumOfRemaining = 0;

        // Calculate total val of remaining slider
        for(let s of this.slider) {
            if(s !== slider) sumOfRemaining += s.value;
        }

        // Normalize other slider based on remaining total val
        if (sumOfRemaining === 0) {
            // Distribute the remainingTotal equally among the remaining slider
            const equalValue = remainingTotal / (this.slider.length - 1);

            for(let s of this.slider) s.value = equalValue;
        } else {
            for(let s of this.slider) {
                if(s !== slider) s.value = (s.value / sumOfRemaining) * remainingTotal;
            }
        }
    }
}

export class CompileOptionCheckbox extends CompileOptionBase {
    constructor(key, title, tooltip, defaultValue) {
        super("Checkbox", key, title, tooltip, defaultValue);
    }
}

export class CompileOptionTextInput extends CompileOptionBase {
    constructor(key, title, tooltip, placeholder, defaultValue) {
        super("TextInput", key, title, tooltip, defaultValue);

        this.placeholder = placeholder;
    }

    getValue() {
        let val = this.value != null ? this.value.trim() : "";
        return val.length > 0 ? val : null;
    }
}

export class CompileOptionTextInputUnit extends CompileOptionBase {
    constructor(key, title, tooltip, placeholder, defaultValue, unit, unitWidth) {
        super("TextInputUnit", key, title, tooltip, placeholder, defaultValue);

        this.placeholder = placeholder;
        this.unit = unit;
        this.unitWidth = unitWidth;
    }

    getValue() {
        let val = this.value != null ? this.value.trim() : "";
        return val.length > 0 ? val : null;
    }
}

export class CompileOptionSelect extends CompileOptionBase {
    constructor(key, title, tooltip, defaultValue, options) {
        super("Select", key, title, tooltip, options.find((el) => el.key === defaultValue));

        this.options = options;
    }

    setValue(newVal) {
        if(typeof newVal !== "object") newVal = this.options.find((el) => el.key === newVal);

        super.setValue(newVal);
    }

    getValue() {
        return this.value.key;
    }
}

export class CompileOptionStrategy {
    constructor(key, title, elements = [], onValueChangedCallback) {
        this.key = key;
        this.title = title;

        this.onValueChangedCallback = onValueChangedCallback;

        let finalElms = [];

        for(let elm of elements) {
            elm.strategy = this;

            finalElms.push(elm);

            if(elm instanceof CompileOptionGrouper) {
                for(let grouperElm of elm.elements) {
                    grouperElm.strategy = this;
                    finalElms.push(grouperElm);
                }
            }
        }

        this.elements = finalElms;
    }

    onElmValueChanged(elm) {
        if(this.onValueChangedCallback != null) this.onValueChangedCallback(elm);
    }

    load() {
        for(let el of this.elements) {
            el.onLoad();
            this.onElmValueChanged(el);
        }
    }

    reset() {
        for(let el of this.elements) el.setValue(el.defaultValue);
    }

    getStrategyData() {
        let settingsOptions = {};

        for(let el of this.elements) {
            if(el.skipOnExport) continue;

            settingsOptions[el.key] = el.getValue();
        }

        return {
            "name": this.key,
            "settings": settingsOptions
        };
    }

    setData(data) {
        for(let el of this.elements) {
            let v = data[el.key];

            if(v != null) el.setValue(v);
        }
    }
}

export function getDefaultPlacementStrategy(sharedOptions) {
    let simOptions= [
        new CompileOptionSlider("coolingRate", "Cooling Rate", "How fast the algorithm converges towards a stable solution. Higher = Slower", 0.95),
        new CompileOptionTextInput("maxIterations", "Max Iterations", "How many iterations the algorithm performs to find the best solution.", "25000", "25000")
    ];

    let bfOptions= [
        new CompileOptionTextInputUnit("maxBfTime", "Max Duration", "Limits the calculation duration of the algorithm.", "60", "60", "s", "35px"),
    ];

    let scoreSliderGroup = new CompileOptionSliderGroup();

    let weightSlider = [
        new CompileOptionSlider("scoreTp", "Throughput", "How significant the algorithm will try to maximize the overall throughput of the pipeline.", 0.5, scoreSliderGroup),
        new CompileOptionSlider("scoreTransfer", "Data Transfer", "How significant the algorithm will try to minimize the overall data transfer costs of the operators.", 0.25, scoreSliderGroup),
        new CompileOptionSlider("scoreNodeCount", "# Executors", "How significant the algorithm will try to minimize the overall utilized executors of the pipeline.", 0.25, scoreSliderGroup)
    ];

    let baseOptions = [
        new CompileOptionGrouper("Placement Weights", "Defines the weights for the placement algorithm to find the best target constellation.", weightSlider),
    ];

    let allOptions = [
        new CompileOptionSelect("algorithm", "Algorithm", "The algorithm to use for calculation.", "SimulatedAnnealing",
            [
                {"key": "Greedy", "title": "Greedy"},
                {"key": "SimulatedAnnealing", "title": "Sim. Annealing"},
                {"key": "BruteForce", "title": "Brute Force"},
                {"key": "Backtracking", "title": "Backtracking"}
            ])
    ].concat(bfOptions).concat(simOptions).concat(baseOptions).concat(sharedOptions)

    let elmChangedCallback = function(elm) {
        if(elm.key === "algorithm") {
            if(elm.value.key === "SimulatedAnnealing") {
                for(let op of simOptions) op.show = true;
            } else {
                for(let op of simOptions) op.show = false;
            }

            if(elm.value.key === "BruteForce") {
                for(let op of bfOptions) op.show = true;
            } else {
                for(let op of bfOptions) op.show = false;
            }
        }
    }

    return new CompileOptionStrategy("default", "Default", allOptions, elmChangedCallback);
}