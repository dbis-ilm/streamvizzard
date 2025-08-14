import {Component} from "@/scripts/components/Component";
import {StringControl} from "@/scripts/components/modules/base/controls/StringCtrl";
import {strSocket} from "@/scripts/components/modules/base";

export default class _FileSink extends Component {
    constructor(pathIdentifier){
        super("FileSink", "File Sink", pathIdentifier);
    }

    builder(node) {
        node.path = new StringControl(node, 'path', false, '', "Path");

        return this.onBuilderInitialized(node,
            null,
            [{name: strSocket.name, socket: strSocket}],
            [],
            [node.path]);
    }
}
