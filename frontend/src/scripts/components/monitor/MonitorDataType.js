export class MonitorDataType {
    constructor(name, displayName) {
        this.name = name;
        this.displayName = displayName;

        this.displayModes = new Map();
    }

    registerDisplayMode(modeID, name, template, props) {
        if(props === undefined) props = {};

        this.displayModes.set(modeID, {name: name, template: template, props: props});
    }

    getDisplayMode(mode) {
        if(!this.displayModes.has(mode)) return null;

        return this.displayModes.get(mode);
    }

    getDisplayModes() {
        return this.displayModes;
    }
}
