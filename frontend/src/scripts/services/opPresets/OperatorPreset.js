export default class OperatorPreset {
    /** @type String **/ category;
    /** @type String **/ name;
    /** @type String **/ descr;
    /** @type Number **/ width;
    /** @type Number **/ height;
    /** @type Object **/ saveData;

    // Enriched
    /** @type String **/ style;

    loadFromData(data) {
        Object.assign(this, data);

        return this;
    }
}