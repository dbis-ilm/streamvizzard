import ELK from 'elkjs';
import {SvInstance} from "@/scripts/StreamVizzard";

export class AutoLayoutPipeline {
    constructor() {
        this.elk = new ELK();
    }

    /** @param {SvOperator} op **/
    convertOp(op) {
        return {
            id: op.id,
            width: op.width,
            height: op.height,
            labels: [
                {
                    text: 'label' in op ? op.label : ''
                }
            ],
            ports: [
                ...op.inputs
                    .map((element, idx) => {
                        let size = element.getSize();

                        return {
                            id: this.getSocketId(element),
                            width: size,
                            height: size,
                            x: 0,
                            y: idx * 5,
                            properties: { side: "WEST"}
                        };
                    }),
                ...op.outputs
                    .map((element, idx) => {
                        let size = element.getSize();

                        return {
                            id: this.getSocketId(element),
                            width: size,
                            height: size,
                            x: 0,
                            y: idx * 5,
                            properties: { side: "EAST"}
                        };
                    })
            ],
            layoutOptions: {
                portConstraints: 'FIXED_POS'
            }
        };
    }

    /** @param {SvConnection} connection **/
    convertCon(connection) {
        const source = this.getSocketId(connection.output);
        const target = this.getSocketId(connection.input);

        return {
            id: connection.id,
            sources: [source],
            targets: [target]
        };
    }

    /** @param {SvSocket} socket **/
    getSocketId(socket) {
        return [socket.id, socket.operator.id, socket.input ? "input": "output"].join('_');
    }

    async layout(props = {}) {
        let ops = SvInstance.pipeline.operators;
        if(ops.length === 0) return;

        const cons = SvInstance.pipeline.connections;

        // Remove all reroutes which can't be auto-arranged

        for(let con of SvInstance.pipeline.connections) con.clearReroutes();

        // Remove groups which can't be respected

        let groups = SvInstance.pipeline.groups.slice(); // Copy since deletion modifies group array
        for(let group of groups) group.remove();

        const graph = {
            id: 'root',
            layoutOptions: {
                'elk.algorithm': 'layered',
                'elk.hierarchyHandling': 'INCLUDE_CHILDREN',
                'elk.edgeRouting': 'POLYLINE',
                ...props
            },
            children: ops.map(n => this.convertOp(n)),
            edges: cons.map(c => this.convertCon(c))
        };

        try {
            const result = await this.elk.layout(graph);

            for(let child of result.children) {
                let op = SvInstance.pipeline.getOperatorByID(child.id);

                op.moveTo(child.x, child.y);
            }
        } catch (error) {
            console.log(error);
        }
    }
}
