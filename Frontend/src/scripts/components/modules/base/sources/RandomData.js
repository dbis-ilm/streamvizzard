import {Component} from "@/scripts/components/Component";
import {STRING_DT, strSocket} from "@/scripts/components/modules/base";
import {Display} from "@/scripts/components/monitor/Display";
import {NumControl} from "@/scripts/components/modules/base/controls/NumberCtrl";
import {BoolControl} from "../controls/BoolCtrl";

export default class _RandomData extends Component {
    constructor(pathIdentifier){
        super("RandomData", "Random Data", pathIdentifier, true);
    }

    builder(node) {
        node.limitRate = new BoolControl(node, 'limitRate', false, 'Limit Rate',
            'If the source should produce tuples in a fixed rate', true);
        node.rate = new NumControl(node, 'rate', false, 30, "Rate",
            "How many data tuples per second are generated.", 0);

        node.limitRate.onChangeCallback = (val) => {
            node.rate.show = val;
        };

        return this.onBuilderInitialized(node,
            new Display(node, STRING_DT.name),
            [],
            [{name: "Data", socket: strSocket}],
            [node.limitRate, node.rate]);
    }
}
