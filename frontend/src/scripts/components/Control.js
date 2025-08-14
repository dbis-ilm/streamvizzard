import Rete from "rete";

export class Control extends Rete.Control {
    constructor(node, editor, key, component, readonly, defaultVal,
                title = "", tooltip = "") {
        super(key);

        this.component = component;
        this.show = true;

        this.onChangeCallback = null;

        this.props = { cKey: key, readonly: readonly, defaultVal: defaultVal,
            description: title, tooltip: tooltip,
            node: node, ctrl: this};

        this.onValueChanged();
    }

    onValueChanged() {
        if(this.onChangeCallback != null) this.onChangeCallback(this.getValue());
    }

    setValue(val) {
        this.vueContext.setData(val); // This triggers data update (if changed)!

        this.onValueChanged();
    }

    getValue() {
        return this.vueContext.value;
    }
}
