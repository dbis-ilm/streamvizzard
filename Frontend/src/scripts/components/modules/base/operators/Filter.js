import {Component} from "@/scripts/components/Component";
import {anySocket} from "@/scripts/components/modules";
import {CodeControl} from "@/scripts/components/modules/base/controls/CodeCtrl";
import {Display} from "@/scripts/components/monitor/Display";

export default class _UDF extends Component {
    constructor(pathIdentifier){
        super("Filter", "Filter", pathIdentifier);
    }

    builder(node) {
        node.code = new CodeControl(node, 'code', false, "return True");

        return this.onBuilderInitialized(node,
            new Display(node),
            [{name: "Any", socket: anySocket}],
            [{name: "Any", socket: anySocket}],
            [node.code]);
    }

    getData(node) {
        return {
            code: node.code.getValue()
        };
    }

    setData(node, data) {
        node.code.setValue(data.code);
    }
}
