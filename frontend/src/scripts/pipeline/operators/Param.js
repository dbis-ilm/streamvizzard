export class Param {
    /** @param {String} key
     * @param {any} defaultVal
     * @param {String} title
     * @param {String|null} tooltip **/
    constructor(key, defaultVal, title, tooltip = "") {
        this.key = key;

        this.tooltip = tooltip;
        this.title = title;

        /** @type SvOperator **/
        this.operator = null;

        this.show = true;

        this.onChangeCallback = null;

        this.value = defaultVal;

        this.onValueChanged();
    }

    getTemplate() {
        console.error("GetTemplate method not implemented for", this.constructor.name);

        return null;
    }

    onValueChanged() {
        if(this.onChangeCallback != null) this.onChangeCallback(this.getValue());
    }

    setValue(val) {
        let oldData = this.value;

        this.value = val;

        if(oldData !== val) {
            this.onValueChanged();

            this.operator.onParamChanged(this, oldData);
        }
    }

    getValue() {
        return this.value;
    }
}
