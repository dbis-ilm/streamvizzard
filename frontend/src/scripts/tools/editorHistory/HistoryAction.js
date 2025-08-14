export default class HistoryAction {
    constructor(editor) {
        this.editor = editor;
    }

    //UI events will not be sent to server and only exist in UI history
    isUIEvent() { return false; }

    // Events that modify the pipelineState structure/operator data
    isPipelineChangeEvent() { return false; }

    async undo() {}

    async redo() {}
}
