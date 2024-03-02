import {getOperatorByID} from "@/components/Main";
import {sleep} from "@/scripts/tools/Utils";
import {AddNodeAction} from "@/scripts/tools/editorHistory/NodeAction";
import {EVENTS, executeEvent} from "@/scripts/tools/EventHandler";

export class TestUtils {
    constructor(editor) {
        this.editor = editor;
    }

    async deletionTest(opID, runs, sleepTime= 0.1, debugging=true, events=true) {
        if(events) executeEvent(EVENTS.UI_HISTORY_TRAVERSE, [true, true]);
        let na = new AddNodeAction(this.editor, getOperatorByID(opID));
        na.debuggingEvent = debugging;

        const start = Date.now();

        for(let i=0; i < runs; i++){
            await na.undo();

            if(sleepTime > 0) await sleep(sleepTime / 2);

            await na.redo();

            if(sleepTime > 0) await sleep(sleepTime / 2);
        }

        const end = Date.now();
        console.log(`Execution time: ${end - start} ms`);
        if(events) executeEvent(EVENTS.UI_HISTORY_TRAVERSE, [false, true]);
    }

    async translateTest(opID, runs, sleepTime= 0.1, events=true) {
        if(events) executeEvent(EVENTS.UI_HISTORY_TRAVERSE, [true, true]);
        // Reduce amount of translates by changing updateID handling on server?
        const start = Date.now();

        let op = getOperatorByID(opID);
        let node = this.editor.view.nodes.get(op);

        let x = Math.random() * 5;
        let y = Math.random() * 5;

        for(let i=0; i < runs; i++){
            node.translate(x, y);
            this.editor.trigger('nodedraged', node);

            if(sleepTime == null) await sleep(sleepTime);
        }

        const end = Date.now();
        console.log(`Execution time: ${end - start} ms`);
        if(events) executeEvent(EVENTS.UI_HISTORY_TRAVERSE, [false, true]);
    }
}
