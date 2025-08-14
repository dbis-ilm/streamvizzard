<template>
  <div id="provInspector" ref="container" :class="opened ? '' : 'hidden'">
    <div class="provTitle">Provenance Inspector
      <div id="provQueryExecute" :class="'noSelect clickableIcon' + (queryExecutable ? '' : ' disabled') + (executingQuery ? ' executing' : '')" @click="_executeQuery()">
        Execute
        <div id="spinnerContainer" v-if="executingQuery"><div class="loader"></div></div></div>
    </div>
    <div class="queryCmdTitle" ref="queryCmdTitle"></div>
    <div class="queryCmdContainer" ref="queryCmdContainer"></div>
    <div class="queryCmdDeleteCond"><i class="ctrlIcon bi bi-x-circle" v-if="selectedChain != null && selectedChain.canBeDeleted()" title="Remove selected chain" @click="_removeChain()"></i></div>
    <div class="queryCmdClear"><i class="ctrlIcon bi bi-trash3" title="Clear query" @click="_clearQuery()"></i></div>
    <div class="queryContainer" ref="queryContainer"></div>
    <div id="loadingOverlay" v-if="executingQuery"></div>
  </div>
</template>

<script>

import {makeGenericResizable} from "@/scripts/tools/Utils";
import $ from "jquery";
import {HistoryGraphDisplayElementType} from "@/components/features/debugger/HistoryGraph.vue";
import {DataExportService} from "@/scripts/services/dataExport/DataExportService";
import {PipelineService} from "@/scripts/services/pipelineState/PipelineService";

const ProvQueryTarget = {
  BEST_BRANCH: {
    "title": "Optimum",
    "key": "Optimum",
    "text": "Find <b>Optimum</b> Return",
    "chains": [
      {"key": "limit", "repeatable": false, "hasBgColor": true, "cmds": [(c, id) => createLimitCmd(c, id, "Best <b>$VAl</b> Where")]},
      {
        "key": "condition",
        "repeatable": true,
        "hasBgColor": true,
        "repeatCmd": createCondLogicChainCmd,
        "cmds": [createCondOpCmd, createCondOpTargetTypeCmd, createCondOpTargetCmd, createCondComparatorCmd, createCondValueCmd]
      }
    ],
    "resultFunc": handleOptimumQueryResult
  },
  UPDATE_IMPACT: {
    "title": "Update Impact",
    "key": "UpdateImpact",
    "text": "Find <b>Update Impact</b> of",
    "chains": [
      {"key": "opTarget", "repeatable": false, "hasBgColor": true, "cmds": [
          (c, id) => createCondOpCmd(c, id, "Op <b>$VAL</b> on"),
          (c, id) => createCondOpTargetTypeCmd(c, id, [ConditionOpTargetTypes.METRIC]),
          createCondOpTargetCmd]
      },
      {"key": "condition", "repeatable": false, "hasBgColor": true, "cmds": [
          (c, id) => createOrderingCmd(c, id, {[ResultOrdering.ASC]: "Worst", [ResultOrdering.DESC]: "Best"}, "Return <b>$VAl</b>"),
          (c, id) => createLimitCmd(c, id, "<b>$VAl Updates</b> With <b>Impact</b>"),
          (c, id) => createCondComparatorCmd(c, id),
          (c, id) => createCondValueCmd(c, id, "<b>$VAL%</b>", "Percentage %")]
      },
    ],
    "resultFunc": handleUpdateResult
  },
}

const ConditionOpTargetTypes = {
  METRIC: "Metric",
  PARAM: "Param",
}

const ConditionOpMetricTypes = {
  THROUGHPUT: {"key": "throughput", "text": "Throughput"},
  AVG_EXECUTION_TIME: {"key": "avgExTime", "text": "AvgExTime"}
}

const ConditionComparator = {
  EQUAL: "=",
  NOT_EQUAL: "<>",
  LESS: "<",
  GREATER: ">",
  LESS_EQUAL: "<=",
  GREATER_EQUAL: ">=",
}

const ConditionLogicChain = {
  AND: "And",
  // OR: "Or", Currently unused, always linked as AND
}

const ResultOrdering = {
  ASC: "Asc",
  DESC: "Desc"
}

const ConditionColorPalette = [
    "rgba(130, 226, 255, 0.9)", "rgba(255, 205, 100, 0.9)",
    "rgba(132,183,252,0.9)", "rgba(207, 139, 246, 0.9)",
    "rgba(255, 140, 128, 0.9)", "rgba(129, 236, 107, 0.9)"];

// --------------- CMD Constructors ---------------

const QueryConditionCmdTypes = {
  OP: "opID",
  OP_TARGET_TYPE: "opTargetType",
  OP_TARGET: "opTargetValue",
  COMPARATOR: "comparator",
  VALUE: "value",
  LOGIC_CHAIN: "logicChain",
  RETURN_ORDER: "returnOrder",
  LIMIT: "limit"
}

function createCondOpCmd(condition, cmdID, cmdTitle="Op <b>$VAL</b>") {
  return new ProvQueryCmd(condition, cmdID, QueryConditionCmdTypes.OP, "Select Operator", function (queryCmd, container) {

    let options = [];

    options.push({"id": "null", "text": "Select Operator"});

    for (let op of PipelineService.getAllOperators()) options.push({"id": op.id, "text": op.viewName + "[" + op.id + "]"});

    createDropdownQueryCmd(container, options, function (event) {
      if(event.target.value === "null") return;

      let opID = parseInt(event.target.value);
      let op = PipelineService.getOperatorByID(opID);

      queryCmd.applyData(opID, cmdTitle.replace("$VAL", op.viewName + "[" + opID + "]"), true);
    });
  }, function(queryCmd, opID) {
    let op = PipelineService.getOperatorByID(opID);
    queryCmd.applyData(opID, cmdTitle.replace("$VAL", op.viewName + "[" + opID + "]"), true);
  });
}

function createCondOpTargetTypeCmd(condition, cmdID, limitTargetTypes=null, cmdTitle="<b>$VAL</b>") {
  return new ProvQueryCmd(condition, cmdID, QueryConditionCmdTypes.OP_TARGET_TYPE,"Select Target Type", function(queryCmd, container) {
    let entries = limitTargetTypes == null ? Object.values(ConditionOpTargetTypes) : limitTargetTypes;

    for(let val of entries) {
      if (val === ConditionOpTargetTypes.PARAM) {
        // Check if operator has params

        let opCmd = condition.getCmdByType(QueryConditionCmdTypes.OP);

        let op = PipelineService.getOperatorByID(opCmd.value);
        let params = op.component.getData(op);

        if (params == null || params.length === 0) continue;
      }

      createTextQueryCmd(container, val, function () {
        queryCmd.applyData(val, cmdTitle.replace("$VAL", val), true);
      });
    }
  }, function(queryCmd, value) {
    queryCmd.applyData(value, cmdTitle.replace("$VAL", value), true);
  });
}

function createCondOpTargetCmd(condition, cmdID) {
  return new ProvQueryCmd(condition, cmdID, QueryConditionCmdTypes.OP_TARGET, "Select Target", function (queryCmd, container) {
    let opCmd = condition.getCmdByType(QueryConditionCmdTypes.OP);
    let op = PipelineService.getOperatorByID(opCmd.value);

    let targetTypeCmd = condition.getCmdByType(QueryConditionCmdTypes.OP_TARGET_TYPE);

    if(targetTypeCmd.value === ConditionOpTargetTypes.METRIC) {
      for(let k in ConditionOpMetricTypes) {
        if(ConditionOpMetricTypes[k] === ConditionOpMetricTypes.THROUGHPUT) { // One TP element for each output
          for(let [,v] of op.outputs.entries()) {
            for(let con of v.connections) {
              createTextQueryCmd(container, ConditionOpMetricTypes[k].text + " (Con " + con.id + ")", function() {
                queryCmd.applyData(ConditionOpMetricTypes[k].key + "_" + con.id, "<b>" + ConditionOpMetricTypes[k].text + " (Out " + con.id + ")</b>");
              }, "Throughput of out connection " + con.id + " from socket " + v.name + " to socket " + con.input.name + " of op " + con.input.node.viewName);
            }
          }
        } else if(ConditionOpMetricTypes[k] === ConditionOpMetricTypes.MESSAGE_Q_SIZE) { // One QSize element for each input
          let i = 0;

          for(let [,v] of op.inputs.entries()) {
            let idx = i;
            createTextQueryCmd(container, ConditionOpMetricTypes[k].text + " (In " + (idx + 1) + ")", function() {
              queryCmd.applyData(ConditionOpMetricTypes[k].key + "_" + idx, "<b>" + ConditionOpMetricTypes[k].text + " (In " + (idx + 1) + ")</b>");
            }, "MessageQueueSize of in socket nr. " + (idx + 1) + " with name " + v.name);

            i += 1;
          }
        } else {
          createTextQueryCmd(container, ConditionOpMetricTypes[k].text, function() {
            queryCmd.applyData(ConditionOpMetricTypes[k].key, "<b>" + ConditionOpMetricTypes[k].text + "</b>");
          });
        }
      }
    } else if(targetTypeCmd.value === ConditionOpTargetTypes.PARAM) {
      let params = op.component.getData(op);

      for(let k in params) {
        createTextQueryCmd(container, k, function() {
          queryCmd.applyData(k, "<b>" + k + "</b>");
        });
      }
    }
  }, function(queryCmd, value) {
    let targetTypeCmd = condition.getCmdByType(QueryConditionCmdTypes.OP_TARGET_TYPE);

    if(targetTypeCmd.value === ConditionOpTargetTypes.METRIC) {
      for(let k in ConditionOpMetricTypes) {
        let typ = ConditionOpMetricTypes[k];

        if(value.startsWith(typ.key)) {
          queryCmd.applyData(value, "<b>" + typ.text + "</b>");

          break;
        }
      }
    } else if(targetTypeCmd.value === ConditionOpTargetTypes.PARAM) queryCmd.applyData(value, "<b>" + value + "</b>");
  });
}

function createCondComparatorCmd(condition, cmdID, cmdTitle="<b>$VAL</b>") {
  return new ProvQueryCmd(condition, cmdID, QueryConditionCmdTypes.COMPARATOR, "Select Target Comparator", function (queryCmd, container) {
    for(let k in ConditionComparator) {
      createTextQueryCmd(container, ConditionComparator[k], function() {
        queryCmd.applyData(ConditionComparator[k], cmdTitle.replace("$VAL", ConditionComparator[k]));
      });
    }
  }, function(queryCmd, value) {
    queryCmd.applyData(value, cmdTitle.replace("$VAL", value));
  });
}

function createCondValueCmd(condition, cmdID, cmdTitle="<b>$VAL</b>", placeholder="Value") {
  return new ProvQueryCmd(condition, cmdID, QueryConditionCmdTypes.VALUE, "Select Target Value", function (queryCmd, container) {
    createInputFieldQueryCmd(container, placeholder, function(event) {
      let val = event.target.value;
      queryCmd.applyData(val, cmdTitle.replace("$VAL", val));
    });
  }, function(queryCmd, value) {
    queryCmd.applyData(value, cmdTitle.replace("$VAL", value));
  });
}

function createLimitCmd(condition, cmdID, cmdTitle="<b>$VAl</b>", title="Select Return Limit") {
  return new ProvQueryCmd(condition, cmdID, QueryConditionCmdTypes.LIMIT, title, function (queryCmd, container) {
    createInputFieldQueryCmd(container, "Number", function(event) {
      let val = event.target.value;
      queryCmd.applyData(val, cmdTitle.replace("$VAl", val));
    });
  }, function(queryCmd, value) {
    queryCmd.applyData(value, cmdTitle.replace("$VAl", value));
  });
}

function createOrderingCmd(condition, cmdID, customCmdLabels=null, cmdTitle="<b>$VAl</b>", title="Select Result Ordering") {
  function findDisplayVal(current) {
    if(customCmdLabels != null) {
      for(let cl in customCmdLabels) {
        if(cl === current) return customCmdLabels[cl];
      }
    }

    return current;
  }

  return new ProvQueryCmd(condition, cmdID, QueryConditionCmdTypes.RETURN_ORDER, title, function (queryCmd, container) {
    for(let o in ResultOrdering) {
      let displayVal = findDisplayVal(ResultOrdering[o]);

      createTextQueryCmd(container, displayVal, function() {
        queryCmd.applyData(ResultOrdering[o], cmdTitle.replace("$VAl", displayVal));
      });
    }
  }, function(queryCmd, value) {
    let displayVal = findDisplayVal(value);

    queryCmd.applyData(value, cmdTitle.replace("$VAl", displayVal));
  });
}

function createCondLogicChainCmd(condition, cmdID) {
  return new ProvQueryCmd(condition, cmdID, QueryConditionCmdTypes.LOGIC_CHAIN, "Select Logical Chain", function (queryCmd, container) {
    for(let k in ConditionLogicChain) {
      createTextQueryCmd(container, ConditionLogicChain[k], function() {
        queryCmd.applyData(ConditionLogicChain[k], "<b>" + ConditionLogicChain[k] + "</b>");
      });
    }
  }, function(queryCmd, value) {
    queryCmd.applyData(value, "<b>" + value + "</b>");
  });
}

// --------------- RESULT Functions ---------------

function handleOptimumQueryResult(query, graph, result) {
  let id = 0;

  for(let r of result["res"]) {
    id++;

    let branchID = r["branchID"];
    let stepID = r["stepID"];
    let stepTime = r["stepTime"];

    let params = r["params"];

    let resString = "Optimum#" + id + " at:\nBranch: " + branchID + "\nStep: " + (stepID + 1) + "\nParams:";

    // Extract metric data

    for(let cond of query.chains) {
      let cmd = cond.getCmdByType(QueryConditionCmdTypes.OP_TARGET);
      if(cmd == null) continue;

      for(let param of params) {
        if(param["name"] === cmd.value) {
          let title = cmd.getRawTitle();
          resString += "\n" + title + ": " + param["value"];
          break;
        }
      }
    }

    graph.registerGraphDisplayElements(HistoryGraphDisplayElementType.StepHighlight, branchID, stepID, stepTime, resString);
  }
}

function handleUpdateResult() {

}

// --- Helper ---

function createTextQueryCmd(container, name, onClick, title=null) {
  let cmd = document.createElement('div');
  cmd.setAttribute("class", "queryCmd");
  cmd.innerHTML = name;
  cmd.onclick = onClick;
  if(title != null) cmd.setAttribute("title", title);

  container.appendChild(cmd);
}

function createInputFieldQueryCmd(container, placeholder, onChange) {
  let cmd = document.createElement('input');
  cmd.setAttribute("class", "queryCmd queryCmdInput");
  cmd.setAttribute("placeholder", placeholder);
  cmd.onchange = onChange;

  container.appendChild(cmd);
}

function createDropdownQueryCmd(container, options, onChange) {
  let cmd = document.createElement('select');
  cmd.setAttribute("class", "queryCmd queryCmdSelect");

  for(let option of options) {
    let op = new Option();
    op.value = option["id"];
    op.text = option["text"];

    cmd.options.add(op);
  }

  cmd.onchange = onChange;

  container.appendChild(cmd);
}

function createQueryElement(txt) {
  let elm = document.createElement('div');
  elm.setAttribute("class", "queryElm");
  elm.innerHTML = txt;

  return elm;
}

// ------------------------------------------------

class ProvQueryCmd {
  constructor(condition, cmdID, cmdType, desc, createSelection, loadFunc) {
    this.condition = condition;
    this.desc = desc;

    this.createSelection = createSelection;
    this.loadFunc = loadFunc;

    this.element = null;

    this.cmdID = cmdID;
    this.cmdType = cmdType;
    this.repeater = false;

    this.value = null;
  }

  getRawTitle() {
    if(this.element == null) return "";

    return this.element.innerHTML.replace("<b>", "").replace("</b>", "");
  }

  showSelection(cmdTitle, container) {
    cmdTitle.innerHTML = this.desc;

    this.createSelection(this, container);
  }

  destroy() {
    if(this.element != null) this.element.remove();
    this.element = null;
    this.value = null;
  }

  isSet() {
    return this.value != null;
  }

  applyData(val, title, purgesSuccessors=false) {
    if(this.value === val) return; // No change in data

    this.value = val;

    this.createQueryElement(title, purgesSuccessors);
  }

  createQueryElement(title, purgesSuccessors=false) {
    if(this.element == null) { // Create new
      this.element = createQueryElement(title);

      this.element.setAttribute("data-cmdID", this.cmdID);
      this.element.setAttribute("data-condID", this.condition.id)

      if(this.condition.config.hasBgColor && !this.repeater) this.element.style.backgroundColor = ConditionColorPalette[this.condition.id % ConditionColorPalette.length];

      // Insert after last element
      this.condition.insertElement(this.element);
    } else { // Update
      this.element.innerHTML = title;

      if(purgesSuccessors) {
        for(let i = this.condition.cmds.length - 1; i >= 0; i--) {
          let cmd = this.condition.cmds[i];

          if(cmd === this) break;

          cmd.destroy();
        }

        this.condition.validatePlaceholder();
      }
    }

    this.condition.sys._onQueryUpdated();
  }
}

class ProvQueryChain {
  constructor(sys, query, id, config) {
    this.config = config;
    this.query = query;
    this.sys = sys;
    this.id = id;
    this.cmds = [];

    let repeaterCmd = null;
    if(config.repeatable) repeaterCmd = config.repeatCmd;

    this.repeatable = repeaterCmd != null;

    // Instantiates the cmd objs
    for(let cmd of config.cmds) this.cmds.push(cmd(this, this.cmds.length));

    // Add repeater cmd if required
    if(repeaterCmd != null) {
      let rCmd = repeaterCmd(this, this.cmds.length);
      rCmd.repeater = true;
      this.cmds.push(rCmd);
    }

    this.placeholderElement = null;
    this.selectedCmd = null;
    this.selected = false;

    this._createPlaceholderElm(sys);
  }

  updateCmdSelection(cmdTitle, container) {
    this.selectedCmd.showSelection(cmdTitle, container);
  }

  getCmdByType(cmdType) {
    for(let cmd of this.cmds) {
      if(cmd.cmdType === cmdType) return cmd;
    }

    return null;
  }

  getCmdByID(cmdID) {
    for(let cmd of this.cmds) {
      if(cmd.cmdID === cmdID) return cmd;
    }

    return null;
  }

  _createPlaceholderElm() {
    this.placeholderElement = document.createElement('div');
    this.placeholderElement.setAttribute("class", "queryElmPlaceholder");
    this.placeholderElement.innerHTML = "<i class='bi bi-box-arrow-in-down'></i>";
    this.placeholderElement.setAttribute("data-condID", this.id);
    this.placeholderElement.setAttribute("title", "Current cursor to add query commands");

    // Find last element to insert behind

    let lastElm = null;

    for(let cmd of this.cmds) {
      if(cmd.isSet()) lastElm = cmd;
    }

    let next = lastElm != null && lastElm.element != null ? lastElm.element.nextSibling : null;

    if(next != null) this.sys.$refs.queryContainer.insertBefore(this.placeholderElement, next);
    else this.sys.$refs.queryContainer.appendChild(this.placeholderElement);
  }

  insertElement(elm) {
    if(this.placeholderElement != null) this.sys.$refs.queryContainer.insertBefore(elm, this.placeholderElement);
    else this.sys.$refs.queryContainer.appendChild(elm);

    if(this.isCompleted()) {
      if(this.query.isLastChain(this)) {
        let newCond = this.query.createNewChain(this.sys);
        this.sys._selectChain(newCond);
      } else this.sys._selectChain(this.query.getLastChain());
    } else this.selectChain(); // Select next empty element

    this.markCmdsSelected(this.selected);

    this.validatePlaceholder();
  }

  validatePlaceholder() {
    // Condition completed, remove placeholder
    if(this.isCompleted()) this._removePlaceholderElm();
    else if(this.placeholderElement == null) this._createPlaceholderElm();

    if(this.placeholderElement != null) {
      if(this.isValid()) this.placeholderElement.classList.remove("queryElmPlaceholderRequired");
      else this.placeholderElement.classList.add("queryElmPlaceholderRequired");
    }
  }

  isCompleted() {
    return this.cmds[this.cmds.length - 1].isSet();
  }

  isEmpty() {
    for(let cmd of this.cmds) {
      if(cmd.isSet()) return false;
    }

    return true;
  }

  isValid(allowEmpty=true) {
    // Chain is valid if all elements are set (in case there are succeeding conditions)
    // or if there are no succeeding conditions the repeater element can be omitted

    let allCmdsSet = true;
    let repeaterSet = false;

    for(let cmd of this.cmds) {
      if(!cmd.repeater && !cmd.isSet()) allCmdsSet = false;
      else if(cmd.repeater) repeaterSet = cmd.isSet();
    }

    if(this.isEmpty()) return allowEmpty;

    if(!allCmdsSet) return false;

    if(repeaterSet || !this.repeatable) return true; // Completed
    else return this.query.isLastChain(this); // Completed if last condition
  }

  canBeDeleted() {
    return this.repeatable && !this.isEmpty();
  }

  selectChain(cmdID = null) {
    if(cmdID == null) {
      $(this.placeholderElement).addClass("queryElmSelected");

      // Find first empty cmd to select (or last by default)

      this.selectedCmd = this.cmds[this.cmds.length - 1];

      for(let cmd of this.cmds) {
        if(!cmd.isSet()) {
          this.selectedCmd = cmd;
          break;
        }
      }
    } else this.selectedCmd = this.getCmdByID(cmdID);

    this.selected = true;

    this.markCmdsSelected(true);
  }

  deselectChain() {
    this.selected = false;

    this.markCmdsSelected(false);

    if(this.placeholderElement == null) return;

    $(this.placeholderElement).removeClass("queryElmSelected");
  }

  markCmdsSelected(selected) {
    for(let cmd of this.cmds) {
      if(cmd.repeater) continue;

      if(cmd.element != null) {
        if(selected) cmd.element.classList.add("queryActiveChain");
        else cmd.element.classList.remove("queryActiveChain");
      }
    }

    if(this.placeholderElement != null) {
      if(selected) this.placeholderElement.classList.add("queryActiveChain");
      else this.placeholderElement.classList.remove("queryActiveChain");
    }
  }

  destroy() {
    this._removePlaceholderElm();

    for(let cmd of this.cmds) cmd.destroy();
  }

  _removePlaceholderElm() {
    if(this.placeholderElement != null) {
      this.placeholderElement.remove();
      this.placeholderElement = null;
    }
  }
}

class ProvQuery {
  constructor() {
    this.target = null;
    this.targetElement = null;

    this.chains = [];
  }

  canExecute() {
    if(this.target == null) return false;

    if(this.chains.length === 0) return false;

    let repeatableCount = 0;
    for(let chain of this.chains) {
      if(chain.repeatable) repeatableCount++;

      let mayEmpty = chain.repeatable && repeatableCount > 1;

      if(!chain.isValid(mayEmpty)) return false;
    }

    return true;
  }

  getQuery() {
    let res = {"target": this.target.key};

    let chains = [];

    for(let cond of this.chains) {
      if(cond.isEmpty()) continue;

      let chain = {"chainKey": cond.config.key};

      for(let cmd of cond.cmds) chain[cmd.cmdType] = cmd.value;

      chains.push(chain);
    }

    res["chains"] = chains;

    return res;
  }

  exportQuery() {
    if(this.target == null) return {};

    let data = {"target": this.target.key};

    let conditions = [];

    for(let chain of this.chains) {
      if(!chain.isEmpty()) conditions.push(chain.cmds);
    }

    data["chains"] = conditions;

    return data;
  }

  importQuery(sys, data) {
    if(Object.keys(data).length === 0) return;

    let target = data["target"];

    // Parse query target

    for(let t in ProvQueryTarget) {
      let v = ProvQueryTarget[t];

      if(v.key === target) {
        this.setQueryTarget(sys, v);

        break;
      }
    }

    if(this.target == null) return;

    // If query target was found parse chains

    let chains = data["chains"];

    if(chains == null || chains.length === 0) return;

    // Clear chains in case we have previous ones
    for(let i = this.chains.length - 1; i >= 0; i--) this.removeChain(this.chains[i], sys);

    for(let conIDX = 0; conIDX < chains.length; conIDX++) {
      let cmds = chains[conIDX];

      if(conIDX >= this.chains.length) this.createNewChain(sys); // Create new conditions if required

      let chain = this.chains[conIDX];

      for(let cmdIdx = 0; cmdIdx < cmds.length; cmdIdx++) {
        let cmdVal = cmds[cmdIdx];

        if(cmdVal == null) continue;

        let cmd = chain.cmds[cmdIdx];

        cmd.loadFunc(cmd, cmdVal);
      }
    }

    sys._onQueryUpdated();
    sys._selectChain(null);
  }

  interpretQueryResults(graph, resultData) {
    if(this.target == null) return;

    return this.target["resultFunc"](this, graph, resultData);
  }

  setQueryTarget(sys, target) {
    let isEdit = false;

    if(this.target == null) this.target = target;
    else if(this.target !== target) {
      sys._selectChain(null);

      for(let cond of this.chains) cond.destroy();

      this.chains = [];
      this.target = target;

      isEdit = true;
    } else return; // No Change

    if(this.targetElement == null && target != null) { // Create new
      let targetElm = createQueryElement(target.text.replace("$TARGET$", target.title));
      sys.$refs.queryContainer.appendChild(targetElm);

      this.targetElement = targetElm;
    } else if(target != null) { // Update
      this.targetElement.innerHTML = target.text.replace("$TARGET$", target.title);
    }

    if(target == null) { // Clear
      if(this.targetElement != null) this.targetElement.remove();
      this.targetElement = null;

      sys._onQueryUpdated();

      return;
    }

    if(this.chains.length === 0) {
      let cond = this.createNewChain(sys);
      if(!isEdit) sys._selectChain(cond);
    }

    sys._onQueryUpdated();
  }

  isLastChain(chain) {
    for(let cID = 0; cID < this.chains.length; cID++) {
      let c = this.chains[cID];

      if(chain === c) return cID === this.chains.length - 1;
    }

    return true;
  }

  getChainByID(id) {
    for(let c of this.chains) {
      if(c.id === id) return c;
    }

    return null;
  }

  getLastChain() {
    return this.chains[this.chains.length - 1];
  }

  getNextChain() {
    // Find correct chain to initialize based on target chain definition

    let chains = this.target.chains;

    let currentChainIdx = 0;
    let targetChain = chains[currentChainIdx];

    for(let c of this.chains) {
      if(c.config.key === targetChain.key) { // Current chain already initialized in query
        if(targetChain.repeatable) return targetChain; // This chain can be repeated -> use this chain to initialize

        currentChainIdx++;

        if(currentChainIdx >= chains.length) return null; // No more chains available

        targetChain = chains[currentChainIdx];
      }
    }

    return targetChain;
  }

  createNewChain(sys) {
    let chain = this.getNextChain();

    if(chain == null) return;

    let newCond = new ProvQueryChain(sys, this, this.chains.length, chain);

    this.chains.push(newCond);

    return newCond;
  }

  removeChain(chain, sys) {
    let idx = this.chains.indexOf(chain);
    if(idx === -1) return;

    let isLastChain = idx === this.chains.length - 1;

    this.chains.splice(idx, 1);

    chain.destroy();

    // Create new chain to allow new repeatable chains to be added
    if(this.chains.length === 0 || isLastChain) this.createNewChain(sys);

    for(let chain of this.chains) chain.validatePlaceholder();

    sys._selectChain(null);
  }
}

export default {
  name: "ProvInspector",
  props: ["debugger"],
  data() {
    return {
      opened: false,
      currentQuery: new ProvQuery(),
      selectedChain: null,
      executingQuery: false,
      queryExecutable: false,
    }
  },

  methods: {
    open() {
      this.opened = true;
    },

    close() {
      this.opened = false;
    },

    reset() {
      this.close();

      this.executingQuery = false;
      this.queryExecutable = false;
    },

    onReceiveQueryResult(result) {
      if(!this.executingQuery) return;

      console.log(result);
      this.currentQuery.interpretQueryResults(this.debugger.historyGraph, result);

      this.debugger.historyGraph.open();

      this.executingQuery = false;
    },

    _onResize() {
      if(!this.opened || this.$refs.container == null) return;

      // Center the container relative to the parent debugging area
      let container = this.$refs.container.getBoundingClientRect();
      let parent = this.$refs.container.parentElement.getBoundingClientRect();

      let centerX = parent.x + parent.width / 2;

      this.$refs.container.style.left = (centerX - container.width / 2) + "px";
    },

    _onQueryUpdated() {
      this._updateQueryCmdSelection();

      this.queryExecutable = this.currentQuery.canExecute();
    },

    _updateQueryCmdSelection() {
      let container = this.$refs.queryCmdContainer;
      let cmdTitle = this.$refs.queryCmdTitle;

      let ths = this;

      // Clear all previous elements
      container.innerHTML = "";
      cmdTitle.innerHTML = "";

      // Generate target
      if(this.currentQuery.target == null || this.selectedChain == null) {
        cmdTitle.innerHTML = "Select Query Target";

        for(let k in ProvQueryTarget) {
          createTextQueryCmd(this.$refs.queryCmdContainer, ProvQueryTarget[k].title, function() {
            ths.currentQuery.setQueryTarget(ths, ProvQueryTarget[k]);
          });
        }
      } else {  // Update Chain content
        let currentCond = this.selectedChain;

        currentCond.updateCmdSelection(cmdTitle, container);
      }
    },

    _removeChain() {
      // We can only remove non-empty, repeatable chains
      if(this.selectedChain == null || !this.selectedChain.canBeDeleted()) return;

      this.currentQuery.removeChain(this.selectedChain, this);
    },

    _clearQuery() {
      this.currentQuery.setQueryTarget(this, null);
    },

    _selectQueryElement(elm) {
      $(this.$refs.queryContainer).find(".queryElmSelected").each(function() {$(this).removeClass("queryElmSelected")});

      // Deselect element -> restore original state (cursor to last chain)
      if(elm == null) {
        this._selectChain(this.currentQuery.getLastChain());

        this._onQueryUpdated();

        return;
      }

      // May both be null if we selected the target
      let condID = elm.getAttribute("data-condID");
      let cmdID = elm.getAttribute("data-cmdID"); // May be null if we select placeholder

      $(elm).addClass("queryElmSelected");

      if(condID === null) this._selectChain(null);
      else if(cmdID == null) this._selectChain(this.currentQuery.getChainByID(parseInt(condID)));
      else this._selectChain(this.currentQuery.getChainByID(parseInt(condID)), parseInt(cmdID));

      this._onQueryUpdated();
    },

    _selectChain(chain = null, cmdID = null) {
      if(this.selectedChain != null) this.selectedChain.deselectChain();

      this.selectedChain = chain;

      if(this.selectedChain != null) this.selectedChain.selectChain(cmdID);
    },

    _executeQuery() {
      if(this.executingQuery || !this.queryExecutable) return;

      this.debugger.historyGraph.clearDisplayElements(); // Clear prev elements

      let query = this.currentQuery.getQuery();

      this.$emit("executeQuery", query);

      this.executingQuery = true;

      console.log(query);
    },
  },

  computed: {
    isOpen: function() {
      return this.opened;
    }
  },

  mounted() {
    this.resizeObserver = new ResizeObserver(this._onResize);
    this.resizeObserver.observe(this.$el);

    this._onResize();

    makeGenericResizable($(this.$refs.container), null, false, "n,e,ne");

    this._onQueryUpdated();

    let ths = this;
    $(this.$el).on('click', '.queryElm, .queryElmPlaceholder', async function(event) {
      event.stopPropagation();

      ths._selectQueryElement(event.currentTarget);
    });

    $(document).click(function(event) {
      if(!ths.opened) return;

      if(!event.target.classList.contains("queryCmd")) ths._selectQueryElement(null);
    });

    $(document).keyup(async function(e) {
      if(e.key === "Escape") ths.close();
    });

    DataExportService.registerDataExporter("provInspectorData",
        function() { return ths.currentQuery.exportQuery(); },
        function(data) { ths.currentQuery.importQuery(ths, data); });
  }
}

</script>

<style scoped>

#provInspector {
  display: flex;
  flex-direction: column;
  z-index: 1;

  height: 150px;
  min-height: 150px;
  min-width: 500px;
  max-width: 100%;
  max-height: 100%;
  width: 40%;

  position: fixed !important;
  top: auto !important;
  bottom: 0 !important;

  border: 2px solid var(--main-border-color);
  background: rgba(247, 247, 247, 0.9);
  border-top-left-radius: var(--window-border-radius);
  border-top-right-radius: var(--window-border-radius);

  padding: 2px;
}

.provTitle {
  font-weight: bold;
  text-align: center;
  margin-bottom: 2px;
  z-index:1;
}

.queryCmdContainer {
  background: rgba(193, 193, 193, 0.5);
  border-radius: var(--button-border-radius);
  width: 100%;
  min-height: calc(1.5em + 6px);
  margin: 8px auto 0;
  text-align: center;
  overflow-y: auto;
  overflow-x: hidden;
}

.queryCmdTitle {
  text-align: center;
  padding: 0;
  margin-bottom: -6px;
  height: 1.5em;
}

.queryContainer {
  margin-top: 4px;
  width: 100%;
  min-height: 50px;
  border: 1px solid var(--main-border-color);
  background: white;
  border-radius: var(--button-border-radius);
  flex-grow: 1;
  text-align: left;
  overflow-y: auto;
  overflow-x: hidden;
}

.queryCmdDeleteCond, .queryCmdClear {
  position: absolute;
  right: 5px;
  top: 25px;
  cursor: pointer;
}

.queryCmdDeleteCond {
  right: 24px;
}

#provQueryExecute {
  position: absolute;
  left: 5px;
  top: 5px;

  cursor: pointer;

  background: var(--window-buton-bg-color);
  border: 1px solid var(--window-buton-border-color);
  border-radius: var(--button-border-radius);
  padding: 2px;
}

#loadingOverlay {
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.5);
  position: absolute;
}

#spinnerContainer {
  position: absolute;
  top: 3px;
  right: -26px;
  height: 100%;
}

#spinnerContainer > .loader {
  width: 20px;
  height: 20px;
  margin: 0;
}

#spinnerContainer > .loader:after {
  background: rgba(250, 250, 250, 0.9);
}

#provQueryExecute.executing {
  opacity: 0.5;
  pointer-events: none;
}

</style>

<style>

.queryCmd,.queryElm,.queryElmPlaceholder {
  cursor: pointer;
  border: 1px solid var(--window-buton-border-color);
  background: var(--window-buton-bg-color);
  border-radius: var(--button-border-radius);
  display: inline-block;
  padding: 1px;
  margin: 2px;
  min-width: 20px;
  text-align: center;
}

.queryCmdInput {
  font-size: 1rem;
  cursor: text;
}

.queryCmdSelect {
  font-size: 1rem;
  cursor: pointer;
}

.queryActiveChain {
  filter: brightness(1.075) drop-shadow(0px 2px 4px rgb(193, 193, 193));
}

.queryElmSelected {
  background: rgba(193, 193, 193, 0.5) !important;
}

.queryElmPlaceholderRequired {
  color: red;
}

</style>
