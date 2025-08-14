import $ from "jquery";
import {PipelineService} from "../services/pipelineState/PipelineService";
import {resetConnectionMonitor} from "../components/monitor/ConnectionMonitor";

export class TestUtils {
    constructor(editor) {
        this.editor = editor;
    }

    prepareScreenshot() {
        $('.node .socketInput, .node .title').css("transform", "scale(1.3)");
        $('.node .socketInput.input-title').css("padding-left", "25px");
        $('.node .socketInput.output-title').css("padding-right", "25px");

        resetConnectionMonitor();

        for(let v of PipelineService.getAllOperators())
            v.component.reset(v, true, false);
    }
}
