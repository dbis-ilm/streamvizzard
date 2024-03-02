import {Component} from "@/scripts/components/Component";
import {STRING_DT, strSocket} from "@/scripts/components/modules/base";
import {StringControl} from "@/scripts/components/modules/base/controls/StringCtrl";
import {Display} from "@/scripts/components/monitor/Display";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";

export default class _HTTPGet extends Component {
    constructor(pathIdentifier){
        super("HTTPGet", "HTTP Get", pathIdentifier, true);
    }

    builder(node) {
        node.url = new StringControl(node, 'url', false, '', "URL");
        node.rate = new NumControl(node, 'rate', false, 5, "Rate",
            "How many requests per second are done", 0)

        return this.onBuilderInitialized(node,
            new Display(node, STRING_DT.name),
            [],
            [{name: "Data", socket: strSocket}],
            [node.url, node.rate]);
    }

    getData(node) {
        return {
            url: node.url.getValue(),
            rate: node.rate.getValue()
        }
    }

    setData(node, data) {
        node.url.setValue(data.url);
        node.rate.setValue(data.rate);
    }
}
