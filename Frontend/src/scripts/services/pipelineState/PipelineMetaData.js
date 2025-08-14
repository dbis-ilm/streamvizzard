import {v4} from 'uuid';

export class PipelineMetaData {
    constructor() {
        this.pipelineName = "";
        this.pipelineUUID = "";

        this.generateNewID();
    }

    updateName(name) {
        this.pipelineName = name;
    }

    getName() {
        return this.pipelineName;
    }

    getUUID() {
        return this.pipelineUUID;
    }

    clear() {
        this.pipelineName = "";
    }

    generateNewID() {
        this.pipelineUUID = v4();
    }
}
