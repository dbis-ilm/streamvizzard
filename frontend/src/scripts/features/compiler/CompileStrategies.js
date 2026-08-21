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

    onLoad() {
    }

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

    onValueChange() {
    }
}

class CompileOptionGrouper extends CompileOptionBaseHelper {
    constructor(title, tooltip, elements) {
        super("Grouper");

        this.tooltip = tooltip;
        this.title = title;

        this.elements = elements;

        this.open = true;
    }

    onToggle() {
        for (let elm of this.elements) elm.show = this.open;
    }
}

class CompileOptionSlider extends CompileOptionBase {
    constructor(key, title, tooltip, defaultValue, sliderGroup = null) {
        super("Slider", key, title, tooltip, defaultValue);

        this.sliderGroup = sliderGroup;

        if (this.sliderGroup != null) this.sliderGroup.registerSlider(this);
    }

    onValueChange(newVal) {
        super.onValueChange(newVal);

        if (this.sliderGroup != null) this.sliderGroup.normalizeSlider(this);
    }
}

class CompileOptionSliderGroup {
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

    normalizeSlider(slider = null) {
        if (!this.hasSlider() || this.slider.length < 2) return;

        if (slider == null) slider = this.slider[0];

        // Limit the total slider values to 1 by keeping the value of the current slider

        let remainingTotal = Math.max(0, 1 - slider.value);
        let sumOfRemaining = 0;

        // Calculate total val of remaining slider
        for (let s of this.slider) {
            if (s !== slider) sumOfRemaining += s.value;
        }

        // Normalize other slider based on remaining total val
        if (sumOfRemaining === 0) {
            // Distribute the remainingTotal equally among the remaining slider
            const equalValue = remainingTotal / (this.slider.length - 1);

            for (let s of this.slider) s.value = equalValue;
        } else {
            for (let s of this.slider) {
                if (s !== slider) s.value = (s.value / sumOfRemaining) * remainingTotal;
            }
        }
    }
}

class CompileOptionCheckbox extends CompileOptionBase {
    constructor(key, title, tooltip, defaultValue) {
        super("Checkbox", key, title, tooltip, defaultValue);
    }
}

class CompileOptionTextInput extends CompileOptionBase {
    constructor(key, title, tooltip, placeholder, defaultValue) {
        super("TextInput", key, title, tooltip, defaultValue);

        this.placeholder = placeholder;
    }

    getValue() {
        let val = this.value != null ? this.value.trim() : "";
        return val.length > 0 ? val : null;
    }
}

class CompileOptionTextInputUnit extends CompileOptionBase {
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

class CompileOptionSelect extends CompileOptionBase {
    constructor(key, title, tooltip, defaultValue, options) {
        super("Select", key, title, tooltip, options.find((el) => el.key === defaultValue));

        this.options = options;
        this.multiple = false;
        this.placeholder = "";
    }

    setValue(newVal) {
        if (typeof newVal !== "object") newVal = this.options.find((el) => el.key === newVal);

        super.setValue(newVal);
    }

    getValue() {
        return this.value.key;
    }
}

class CompileOptionMultiSelect extends CompileOptionSelect {
    constructor(key, title, tooltip, placeholder, defaultValues, options) {
        super(key, title, tooltip, options[0].key, options);

        // defaultValues==null => All, Empty = None
        let dv = [];

        if(defaultValues != null) {
            for(let v of defaultValues) {
                dv.push(options.find((el) => el.key === v))
            }
        } else dv = options;

        this.multiple = true;
        this.placeholder = placeholder;
        this.defaultValue = dv;
        this.value = this.defaultValue;
    }

    setValue(newVal) {
        for(let i = newVal.length; i >= 0; i--) {
            // Only apply values that are present in the option array
            if (typeof newVal[i] !== "object") {
                let option = this.options.find((el) => el.key === newVal[i]);

                if(option != null) newVal[i] = option;
                else newVal.splice(i, 1);
            }
        }

        this.value = newVal;
    }

    getValue() {
        return this.value.map(o => o.key);
    }
}

export class CompileOptionStrategy {
    constructor(key, title, elements = [], onValueChangedCallback) {
        this.key = key;
        this.title = title;

        this.onValueChangedCallback = onValueChangedCallback;

        let finalElms = [];

        for (let elm of elements) {
            elm.strategy = this;

            finalElms.push(elm);

            if (elm instanceof CompileOptionGrouper) {
                for (let grouperElm of elm.elements) {
                    grouperElm.strategy = this;
                    finalElms.push(grouperElm);
                }
            }
        }

        this.elements = finalElms;
    }

    onElmValueChanged(elm) {
        if (this.onValueChangedCallback != null) this.onValueChangedCallback(elm);
    }

    load() {
        for (let el of this.elements) {
            el.onLoad();
            this.onElmValueChanged(el);
        }
    }

    reset() {
        for (let el of this.elements) el.setValue(el.defaultValue);
    }

    getStrategyData() {
        let settingsOptions = {};

        for (let el of this.elements) {
            if (el.skipOnExport) continue;

            settingsOptions[el.key] = el.getValue();
        }

        return {
            "name": this.key,
            "settings": settingsOptions
        };
    }

    setData(data) {
        for (let el of this.elements) {
            let v = data[el.key];

            if (v != null) el.setValue(v);
        }
    }
}

function getSharedPlacementStrategyOptions() {
    let sharedTransferPenalties = [
        new CompileOptionTextInputUnit("avgNodeTransferSpeed", "Node Speed", "The data rate for inter-node communication.", "100", "100", "MB/s", "50px"),
        new CompileOptionTextInputUnit("avgNodeTransferLatency", "Node Latency", "The latency for inter-node communication.", "0.25", "0.25", "ms", "35px"),
        new CompileOptionTextInputUnit("avgConnectorTransferSpeed", "Conn. Speed", "The data rate for connector communication.", "100", "100", "MB/s", "50px"),
        new CompileOptionTextInputUnit("avgConnectorTransferLatency", "Conn. Latency", "The latency for connector communication.", "5", "5", "ms", "35px")
    ];

    let sharedGeneral = [
        new CompileOptionMultiSelect("targetFrameworks", "Frameworks", "Which target frameworks to include in the suggestions.",
            "Select Options...", null,
            [
                {"key": "StreamVizzard", "title": "StreamVizzard"},
                {"key": "PyFlink", "title": "PyFlink"},
            ]),
        new CompileOptionTextInput("maxNodesCount", "Max Executors", "How many processing nodes are available in total for the final execution.", "Unlimited", "10"),
        new CompileOptionTextInput("costModelPath", "Cost Models", "The path for the costModels to consider during calculation.", "/Path/To/Folder"),
    ];

    return [
        new CompileOptionGrouper("Data Transfer Rates", "Defines various data transfer rates an latency for the pipeline.", sharedTransferPenalties),
        new CompileOptionGrouper("General", "General placement options", sharedGeneral)
    ];
}

// ----------------------------------------------------- Strategies ----------------------------------------------------

let sharedPlacementOptions = getSharedPlacementStrategyOptions();

function getDefaultPlacementStrategy() {
    let simOptions = [
        new CompileOptionSlider("coolingRate", "Cooling Rate", "How fast the algorithm converges towards a stable solution. Higher = Slower", 0.95),
        new CompileOptionTextInput("maxIterations", "Max Iterations", "How many iterations the algorithm performs to find the best solution.", "25000", "25000")
    ];

    let bfOptions = [
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
    ].concat(bfOptions).concat(simOptions).concat(baseOptions).concat(sharedPlacementOptions);

    let elmChangedCallback = function (elm) {
        if (elm.key === "algorithm") {
            if (elm.value.key === "SimulatedAnnealing") {
                for (let op of simOptions) op.show = true;
            } else {
                for (let op of simOptions) op.show = false;
            }

            if (elm.value.key === "BruteForce") {
                for (let op of bfOptions) op.show = true;
            } else {
                for (let op of bfOptions) op.show = false;
            }
        }
    }

    return new CompileOptionStrategy("default", "Default", allOptions, elmChangedCallback);
}

export const placementStrategies = [getDefaultPlacementStrategy()];

export const compileStrategies = [new CompileOptionStrategy("default", "Default", [new CompileOptionCheckbox("mergeCluster", "Merge Cluster", "Merges sub-pipelines of same frameworks together, if possible.", true)]),]

export function getStrategyByName(name, placement) {
    let options = placement ? placementStrategies : compileStrategies;

    for(let option of options) {
        if(option.key === name) return option;
    }

    return null;
}
