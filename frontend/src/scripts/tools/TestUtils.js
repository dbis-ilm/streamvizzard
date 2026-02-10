import $ from "jquery";
import {SvInstance} from "@/scripts/StreamVizzard";

export class TestUtils {
    prepareScreenshot() {
        $('.node .socketInput, .node .title').css("transform", "scale(1.3)");
        $('.node .socketInput.input-title').css("padding-left", "25px");
        $('.node .socketInput.output-title').css("padding-right", "25px");

        for(let v of SvInstance.pipeline.operators)
            v.resetState(true);
    }
}
