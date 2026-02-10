export default class HistoryAction {
    constructor() {
        this.time = Date.now();
        this.closed = false;
    }

    //UI events will not be sent to server and only exist in UI history
    isUIEvent() { return false; }

    // Events that modify the pipelineState structure/operator data
    isPipelineChangeEvent() { return false; }

    // Returns true, if the undo had any effect
    async undo() { return true; }

    // Returns true, if the redo had any effect
    async redo() { return true; }
}
