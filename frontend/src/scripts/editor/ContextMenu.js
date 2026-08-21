import {SvInstance} from "@/scripts/StreamVizzard";
import {v4} from "uuid";
import {MODALS} from "@/scripts/interface/Interface";
import SvOperator from "@/scripts/pipeline/operators/SvOperator";


export class ContextMenu {
    /** @param {boolean} showSearchbar
     * @param {Number} posX
     * @param {Number} posY
     * @param {object} type
     * @param {String|null} headerTitle */
    constructor(showSearchbar, posX, posY, type, headerTitle=null) {
        this.id = v4(); // Uniquely identify menu for re-creation

        this.type = type;

        this.showSearchbar = showSearchbar;
        this.headerTitle = headerTitle;
        this.delay = 50;

        this.items = []; // [name, func, path]

        this.posX = posX;
        this.posY = posY;
    }

    _addItem(name, func, path=null, description=null) {
        this.items.push([name, func, path != null ? path : [], description]);
    }
}

export class MainContextMenu extends ContextMenu {
    /** @param {number} posX
     * @param {number} posY
     * @param {Object} [options]
     * @param {number|null} [options.forceId]
     * @param {Object|null} [options.forcePos]
     * @param {Function|null} [options.preCreatedCb]
     * @param {Function|null} [options.postCreatedCb]
     */
    constructor(posX, posY, {
        forceId = null, forcePos = null,
        preCreatedCb = null, postCreatedCb = null} = {}) {

        super(true, posX, posY, ContextMenuType.MAIN_MENU, "Create Operator");

        let createPos = forcePos != null ? forcePos : SvInstance.editor.getEditorPos({x: posX, y: posY});

        for(const definition of SvInstance.modules.opDefinitions) {
            this._addItem(definition.displayName, async () => {
                if(preCreatedCb != null) preCreatedCb(definition);

                let op = await SvInstance.pipeline.createOperator(definition, {id: forceId, x: createPos.x, y: createPos.y});

                if(postCreatedCb != null) postCreatedCb(op);
            }, definition.contextPath, definition.description);
        }
    }
}

export class OperatorContextMenu extends ContextMenu {
    /** @param {number} posX
     * @param {number} posY
     * @param {SvOperator} operator **/
    constructor(posX, posY, operator) {
        super(false, posX, posY, ContextMenuType.OP_MENU, "Operator");

        this._addItem("Duplicate", async () => {
            let newOps = [];

            /** @type {Set<SvConnection>} **/
            let innerCons = new Set();
            /** @type {Map<SvOperator, SvOperator>} **/
            let newOldOpLookup = new Map();

            for(let obj of SvInstance.editor.focusedObjects) {
                if(!(obj instanceof SvOperator)) continue;

                // Register all cons that are contained within the selection
                for(let con of obj.getAllConnections()) {
                    if(SvInstance.editor.focusedObjects.has(con.input.operator) &&
                        SvInstance.editor.focusedObjects.has(con.output.operator)) innerCons.add(con);
                }

                let sd = obj.exportSaveData();

                sd["posX"] = obj.posX + 25;
                sd["posY"] = obj.posY + 25;

                let newOp = await SvInstance.pipeline.createOperatorFromSaveData(sd, false);
                if(newOp == null) continue;

                newOps.push(newOp);
                newOldOpLookup.set(obj, newOp);
            }

            let elmSelection = [];

            for(let newOp of newOps) elmSelection.push(newOp);

            for(let innerCon of innerCons) {
                let newInput = newOldOpLookup.get(innerCon.input.operator);
                let newOutput = newOldOpLookup.get(innerCon.output.operator);

                let con = SvInstance.pipeline.createConnection(newInput.inputs[innerCon.input.id], newOutput.outputs[innerCon.output.id]);

                for(let pin of innerCon.reroutes) elmSelection.push(con.addReroutePin(pin.x + 25, pin.y + 25));
            }

            // Select copied equivalent to orig
            elmSelection.push(newOldOpLookup.get(SvInstance.editor.selectedOperator));

            SvInstance.editor.selectEditorObject(elmSelection);
        });

        // Replace will keep the same operator/connection IDs which triggers restore of existing operators in backend if the pipeline is running
        if(SvInstance.editor.focusedObjects.size === 1 && SvInstance.pipeline.isPipelineStopped()) {
            this._addItem("Replace", () => {
                // Save connection data to restore
                let conSaveData = [];

                for(let socket of [...operator.inputs].concat([...operator.outputs])) {
                    for(let con of socket.connections) conSaveData.push(con.exportSaveData());
                }

                let compileSaveData = operator.compiler.exportSaveData();

                let preCreate = function() {
                    // Remove old operator
                    SvInstance.pipeline.deleteOperator(operator);
                };

                /** @param {SvOperator} newOp **/
                let postCreated = (newOp) => {
                    newOp.uuid = operator.uuid;
                    newOp.compiler.importSaveData(compileSaveData);

                    // Only keep name if it's not the default operator name

                    if(operator.name !== operator.definition.displayName) newOp.name = operator.name;

                    // Re-Create connections

                    for(let conData of conSaveData) SvInstance.pipeline.createConnectionFromSaveData(conData, true);
                };

                let forcePos = {x: operator.posX, y: operator.posY};

                SvInstance.editor.openMainContextMenu(posX, posY,
                    {forceId: operator.id, forcePos, preCreatedCb: preCreate, postCreatedCb: postCreated});
            });
        }

        if(operator.group == null) {
            this._addItem("Group", () => {
                let newGroup = SvInstance.pipeline.createGroup(operator);

                // Add all focused operators to the SAME group

                for(let obj of SvInstance.editor.focusedObjects) {
                    if(obj instanceof SvOperator && obj !== operator) {
                        if(obj.group != null) obj.group.removeOperator(obj); // Remove prev group

                        newGroup.addOperator(obj);
                    }
                }
            });
        }

        if(operator.group != null) {
            this._addItem("Ungroup", () => {
                // Remove group of all focused operators

                for(let obj of SvInstance.editor.focusedObjects) {
                    if(obj instanceof SvOperator && obj.group != null) obj.group.removeOperator(obj);
                }
            });
        }

        if(SvInstance.editor.focusedObjects.size === 1) {
            this._addItem("Store Preset", () => {
                SvInstance.interface.openModal(MODALS.OP_PRESET_STORE, operator);
            });
        }

        this._addItem("Disconnect", () => {
            for(let obj of SvInstance.editor.focusedObjects) {
                if(obj instanceof SvOperator) {
                    for(let con of obj.getAllConnections()) SvInstance.pipeline.deleteConnection(con);
                }
            }
        });

        this._addItem("Delete", () => {
            let focused = SvInstance.editor.focusedObjects; // Store since delete will reset this

            // Remove all focused operators (does not remove selected reroutes)

            for(let obj of focused) {
                if(obj instanceof SvOperator) SvInstance.pipeline.deleteOperator(obj);
            }
        });
    }
}

export class GroupContextMenu extends ContextMenu {
    /** @param {number} posX
     * @param {number} posY
     * @param {Group} group **/
    constructor(posX, posY, group) {
        super(false, posX, posY, ContextMenuType.GROUP_MENU, "Group");

        this._addItem("Collapse", () => {
            for(let op of Object.values(group.operators)) {
                op.showData = false;
                op.showSettings = false;
            }
        });

        this._addItem("Expand", () => {
            for(let op of Object.values(group.operators)) {
                op.showData = true;
                op.showSettings = true;
            }
        });

        this._addItem("Ungroup", () => {
            group.remove();
        });

        this._addItem("Delete", () => {
            for(let op of Object.values(group.operators))
                SvInstance.pipeline.deleteOperator(op);
        });
    }
}

export class ConnectionContextMenu extends ContextMenu {
    /** @param {number} posX
     * @param {number} posY
     * @param {SvConnection} con **/
    constructor(posX, posY, con) {
        super(false, posX, posY, ContextMenuType.CON_MENU, "Connection");

        this._addItem("Insert Operator", () => {
            /** @param {SvOperator} newOp **/
            let opCreatedCb = (newOp) => {
                let oldOutput = con.output;
                let oldInput = con.input;

                SvInstance.pipeline.deleteConnection(con);

                if(newOp.inputs.length > 0) SvInstance.pipeline.createConnection(newOp.inputs[0], oldOutput);
                if(newOp.outputs.length > 0) SvInstance.pipeline.createConnection(oldInput, newOp.outputs[0]);
            };

            let forcePos = SvInstance.editor.getEditorPos({x: posX, y: posY});

            SvInstance.editor.openMainContextMenu(posX, posY,{forcePos, postCreatedCb: opCreatedCb});
        });

        this._addItem("Clear Reroutes", () => {
            con.clearReroutes()
        });

        this._addItem("Delete", () => {
            SvInstance.pipeline.deleteConnection(con);
        });
    }
}

export const ContextMenuType = {
    MAIN_MENU: 0,
    OP_MENU: 1,
    GROUP_MENU: 2,
    CON_MENU: 3
}
