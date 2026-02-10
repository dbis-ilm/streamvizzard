export class ViewConnector {
    constructor() {
        /** @param {function(string): any|null} **/
        this._callback = null;
    }

    /** @param {function(string): any} callback **/
    connect(callback) {
        this._callback = callback;
    }

    /** param {String} identifier **/
    request(identifier) {
        if(this._callback != null) return this._callback(identifier);

        return null;
    }
}