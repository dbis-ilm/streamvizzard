import {v4} from "uuid";

export default class TemplateHost {
    constructor() {
        this.templateKey = v4(); // Unique key to identify instance
    }
}