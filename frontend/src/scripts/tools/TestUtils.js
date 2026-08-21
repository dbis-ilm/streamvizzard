import $ from "jquery";
import {SvInstance} from "@/scripts/StreamVizzard";

export class TestUtils {
    prepareScreenshot(includeDebugger=false,scale=true) {
        if(scale) $('.node').css("width", "75%");

        $('.node .socketInput, .node .title').css("transform", "scale(1.3)");
        $('.node .socket.input .socketInput').css("transform-origin", "left");
        $('.node .socket.output .socketInput').css("transform-origin", "right");

        if(includeDebugger) {
            $('#pipelineDebugger .vue-slider-dot-tooltip').css("visibility", "visible").css("opacity", "1");
            $('#pipelineDebugger .vue-slider-dot-tooltip span').css("font-size", "16px");
        }

        for(let v of SvInstance.pipeline.operators)
            v.resetState(true);
    }
}
