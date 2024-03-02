import Rete from "rete";

export class Control extends Rete.Control {
    constructor(node, emitter, key, component, readonly, defaultVal, description = "", tooltip = "") {
        super(key);

        this.component = component;
        this.props = { emitter: emitter, ikey: key,
            readonly: readonly, defaultVal: defaultVal,
            description: description, tooltip: tooltip,
            node: node, ctrl: this};
    }

    setValue(val) {
        this.vueContext.value = val;
    }

    getValue() {
        return this.vueContext.value;
    }
}
