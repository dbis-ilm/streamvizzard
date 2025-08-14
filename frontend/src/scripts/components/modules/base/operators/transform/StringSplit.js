import {Component} from "@/scripts/components/Component";
import {STRING_DT, strSocket} from "@/scripts/components/modules/base";
import {Display} from "@/scripts/components/monitor/Display";
import {StringControl} from "@/scripts/components/modules/base/controls/StringCtrl";
import {anySocket} from "@/scripts/components/modules";

export default class _StringSplit extends Component {
    constructor(pathIdentifier){
        super("StringSplit", "String Split", pathIdentifier);
    }

    builder(node) {
        node.delimiter = new StringControl(node, "delimiter", false, ",","Delim", "");

        return this.onBuilderInitialized(node,
            new Display(node, STRING_DT.name),
            [{name: strSocket.name, socket: strSocket}],
            [{name: "Array", socket: anySocket}],
            [node.delimiter]);
    }
}
