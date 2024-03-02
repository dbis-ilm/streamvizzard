<template>
<div id="historyGraphContainer" ref="container" :class="opened ? '' : 'hidden'">
  <div ref="content" @mousedown="_onMouseDown" @mousemove="_onMouseMove"
       @mouseup="_onMouseUp" @wheel="_onMouseScroll" @mouseleave="_onMouseLeave"
       :style="'width: calc(100% - ' + 2 * paddingX + 'px); height: calc(100% - ' + (2 * paddingY + 30) + 'px); margin: ' + paddingY + 'px ' + paddingX +'px; overflow: hidden;'">
    <div :class="'clickableIcon'" title="Reset the viewport to the original position" @click="_resetViewport" style="z-index: 1; top: 0; right: 2px; position: absolute; opacity: 0.5;"><i class="bi bi-align-center"></i></div>
    <div id="historyGraph" ref="graph">
      <svg id="historyGraphSVG" ref="svg"></svg>
    </div>
  </div>
  <div id="historyTimeline" :style="'width: calc(100% - ' + 2 * paddingX + 'px);'">
    <div class="historyTl">
      <span ref="tlLeftText" class="historyTlText" title="The delta real time between the actual pipeline execution state and the most left visible debug step." style="left: 3px;"></span>
      <div class="historyTlBorder" style="left: 0;"></div>
      <span ref="tlCenterText" class="historyTlText" style="text-align: center; left:0; width: 100%;"></span>
      <div class="historyTlBorder" style="right: 0;"></div>
      <span ref="tlRightText" class="historyTlText" title="The delta real time between the actual pipeline execution state and the most right visible debug step."  style="right: 3px;"></span>
      <span id="historyTimelineMarker" ref="timelineMarker"></span>
    </div>
  </div>
</div>
</template>

<script>

// TODO: DISALLOW PREVIEW DURING REWINDER
// TODO: SPEEDUP UNDO/REDO BY NOT CREATING NEW OPERATORS INSTANCES EVERY TIME?

import {distance, formatTime, makeGenericResizable} from "@/scripts/tools/Utils";
import $ from "jquery";
import {system} from "@/main";
import {synchronizeExecution} from "@/scripts/tools/debugger/DebuggingUtils";

class HistoryBranch {
  constructor(id, depth, parent, startTime, endTime, stepCount, stepOffset, lineObj, container) {
    this.id = id;
    this.parent = parent;
    this.depth = depth;
    this.lineObj = lineObj;
    this.container = container;
    this.progressContainer = null;
    this.startTime = startTime;
    this.endTime = endTime;
    this.stepCount = stepCount;
    this.stepOffset = stepOffset;

    this.bounds = {};

    this.children = [];
    this.splits = [];
    this.updates = []; // Ordered by step/time

    this.hasChangedData = false;

    this.updateTooltip();
  }

  registerSplit(split) {
    this.splits.push(split);
  }

  registerChild(branch) {
    this.children.push(branch);
  }

  unregisterChild(child) {
    let idx = this.children.indexOf(child);

    if(idx > -1) this.children.splice(idx, 1);
  }

  getSplitStepForChild(child) {
    for(let split of this.splits) {
      if(split.toBranch === child) return split.splitStep;
    }

    return null;
  }

  registerUpdates(stepID, stepTime, updates) {
    this.updates.push(new HistoryPipelineUpdate(stepID, stepTime, updates, this));
  }

  markCurrentState(isCurrent, stepTime) {
    if(isCurrent) {
      this.lineObj.classList.add("historyGraphCurrentBranch");

      if(this.progressContainer == null) {
        this.progressContainer = document.createElement('div');
        this.progressContainer.setAttribute("class", "historyGraphCurrentProgress");

        this.container.prepend(this.progressContainer);
      }

      let timeRange = this.timeRange();
      let fill = timeRange > 0 ? Math.min(100,  (Math.max(0, (stepTime - this.startTime)) / timeRange) * 100) : 0;
      this.progressContainer.style.width = fill + "%";
    } else {
      this.lineObj.classList.remove("historyGraphCurrentBranch");

      if(this.progressContainer != null) {
        this.progressContainer.remove();
        this.progressContainer = null;
      }
    }

    this.updateTooltip();
  }

  updateData(graph, startTime, endTime, stepCount, stepOffset) {
    this.startTime = startTime;
    this.endTime = endTime;
    this.stepCount = stepCount;
    this.stepOffset = stepOffset;

    if(!graph.opened) {
      this.hasChangedData = true;

      return;
    }

    this.hasChangedData = false;

    this.updateTooltip();

    this.updateXPosition(graph);

    // New endTime might force a new depth if current depth is occupied
    let newDepth = graph._findEmptyDepth(this.depth, this, false);

    if(newDepth !== this.depth) {
      this.updateDepth(graph, newDepth);
      graph._updateYPositions(); // Recalculate all positions since depth changed
    }

    graph._updateGraphTime();
  }

  updateDepth(graph, newDepth) {
      this.depth = newDepth;

      this.updateYPosition(graph);

      // Update children recursive..
      for(let child of this.children) {
        if(child.depth > this.depth) continue; // No need to update if child is still on higher depth as parent

        let newDepth = graph._findEmptyDepth(this.depth + 1, child, false);
        if(newDepth !== child.depth) child.updateDepth(graph, newDepth);
      }
  }

  updateSplitPositions(graph) {
    // Update both the splits of us and the parent wo might have splits to us

    if(this.parent != null) {
      for(let s of this.parent.splits) {
        if(s.toBranch === this) s.updatePosition(graph.splitLineWidth);
      }
    }

    for(let s in this.splits) this.splits[s].updatePosition(graph.splitLineWidth);
  }

  updatePipelineUpdates() {
    for(let s in this.updates) this.updates[s].updateXPosition(this);
  }

  updateTooltip() {
    let current = this.progressContainer != null;

    this.container.setAttribute("title", (current ? "Current " : "") + "Branch " + this.id + " with " + this.stepCount + " steps");
  }

  updateXPosition(graph, updateSplits=true) {
    this.lineObj.style.visibility = this.stepCount > 0 ? "Visible" : "Hidden";
    this.container.style.visibility = this.stepCount > 0 ? "Visible" : "Hidden";

    if(this.stepCount > 0) {
      let fromX = graph.visualWidth * graph._timeToXPos(this.startTime);
      let toX = graph.visualWidth * graph._timeToXPos(this.endTime);

      this.lineObj.setAttribute("x1", "" + fromX);
      this.lineObj.setAttribute("x2", "" + toX);

      let width = toX - fromX;

      this.container.style.left = fromX + "px";
      this.container.style.width = width + "px";

      this.bounds["x"] = fromX;
      this.bounds["width"] = width;
    }

    if(updateSplits) this.updateSplitPositions(graph);
    this.updatePipelineUpdates();
  }

  updateYPosition(graph, updateSplits=true) {
    let lineHeight = graph.visualHeight / (graph.depthOccupation.size);

    let y = (graph.depthLevelLookup[this.depth] * lineHeight + lineHeight / 2.0);
    let height = lineHeight * graph.branchHeight;

    this.lineObj.setAttribute("y1", "" + y);
    this.lineObj.setAttribute("y2", "" + y);
    this.lineObj.setAttribute("stroke-width", "" + height);

    let left = (y - height / 2.0);

    this.container.style.top = left + "px";
    this.container.style.height = height + "px";

    this.bounds["y"] = left;
    this.bounds["height"] = height;

    if(updateSplits) this.updateSplitPositions(graph);
  }

  timeRange() {
    return this.endTime - this.startTime;
  }

  destroy() {
    this.lineObj.remove();
    this.container.remove();
    if(this.progressContainer != null) this.progressContainer.remove();

    if(this.parent != null) this.parent.unregisterChild(this);

    for(let s in this.splits) this.splits[s].destroy();

    for(let [, value] of Object.entries(this.updates)) value.destroy();
  }
}

class HistorySplit {
  constructor(fromBranch, toBranch, splitStep, splitTime, lineObj, container) {
    this.fromBranch = fromBranch;
    this.toBranch = toBranch;
    this.lineObj = lineObj;
    this.container = container;
    this.splitStep = splitStep
    this.splitTime = splitTime;
  }

  updatePosition(strokeWidth) {
    let visible = this.fromBranch.stepCount > 0 && this.toBranch.stepCount > 0;
    this.lineObj.style.visibility = !visible ? "Hidden" : "Visible";
    this.container.style.visibility = !visible ? "Hidden" : "Visible";

    if(!visible) return;

    let startXFromBranch = this.fromBranch.bounds["x"] + this.fromBranch.bounds["width"] * (this.splitTime - this.fromBranch.startTime) / this.fromBranch.timeRange();
    let x1 = startXFromBranch + strokeWidth / 2.0;
    let x2 = this.toBranch.bounds["x"] + strokeWidth / 2.0;

    let y1 = this.fromBranch.bounds["y"] + this.fromBranch.bounds["height"];
    let y2 = this.toBranch.bounds["y"];

    let lineHeight = y2 - y1;
    let slopeFac = 0.5; // The higher [0,0.5] the more smooth is the curve

    let leftCtrl = x1 + " " + (y1 + lineHeight * slopeFac);
    let rightCtrl = x2 + " " + (y2 - lineHeight * slopeFac);
    this.lineObj.setAttribute("d", "M " + x1 + " " + y1 + " C " + leftCtrl + ", " + rightCtrl + ", " + x2 + " " + y2);

    this.container.style.left = startXFromBranch + "px";
    this.container.style.width = strokeWidth + "px";
    this.container.style.top = this.fromBranch.bounds["y"] + "px";
    this.container.style.height = this.fromBranch.bounds["height"] + "px";//(y2 - y1) + "px";

    // Split step + 1 to match UI steps starting at id 1
    this.container.setAttribute("title", "Split branch " + this.fromBranch.id + " into branch "
        + this.toBranch.id + " at step " + (this.splitStep - this.toBranch.stepOffset + 1));
  }

  destroy() {
    this.lineObj.remove();
    this.container.remove();
  }
}

class HistoryPipelineUpdate {
  constructor(stepID, stepTime, updateEvents, branch) {
    this.stepID = stepID;
    this.stepTime = stepTime;
    this.updateEvents = updateEvents;

    let hasPipelineChangeEvent = false;

    for(let event of updateEvents) {
      if(event.isPipelineChangeEvent()) {
        hasPipelineChangeEvent = true;
        break;
      }
    }

    if(hasPipelineChangeEvent) {
      this.overlay = document.createElement('div');
      this.overlay.setAttribute("class", "historyGraphPipelineUpdate");
      this.overlay.setAttribute("title", "Pipeline Update at step " + ((this.stepID - branch.stepOffset) + 1));
      this.overlay.setAttribute("branchID", branch.id);
      this.overlay.setAttribute("stepID", stepID);
      branch.container.appendChild(this.overlay);

      this.updateXPosition(branch);
    }
  }

  updateXPosition(branch) {
    if(this.overlay == null) return;

    let timeRange = branch.timeRange();
    let xOff = timeRange > 0 ? Math.min(100,  (Math.max(0, (this.stepTime - branch.startTime)) / timeRange) * 100) : 0;
    this.overlay.style.left = xOff + "%";
  }

  destroy() {
    if(this.overlay != null) this.overlay.remove();
  }
}

class HistoryPipelineUpdateViewer {
  constructor(system) {
    this.system = system;

    this.currentBranch = null;
    this.currentStepID = 0;

    this.origBranch = null;
    this.origStepID = 0;

    this.editor = $('#editor');
  }

  async setCurrentState(branch, stepID, register) {
    await this.reset();

    this.origBranch = branch;
    this.origStepID = stepID;

    // Initial or registering during execution

    if(this.currentBranch == null || register) {
      this.currentBranch = branch;
      this.currentStepID = stepID;
    }

    if(!this.hasPreview()) return;

    await this._traverseTo(branch, stepID);

    if(this.currentStepID !== stepID || this.currentBranch !== branch) console.error("Target step / branch not reached!");
  }

  hasPreview() {
    return this.currentBranch !== this.origBranch || this.currentStepID !== this.origStepID;
  }

  async reset() {
    if(!this.hasPreview()) return;

    this.system.$emit("onHistoryTraversal", true);
    await this._traverseTo(this.origBranch, this.origStepID);
    this.system.$emit("onHistoryTraversal", false);
  }

  async showPreview(branch, targetTime) {
    this.system.$emit("onHistoryTraversal", true);

    if(this.currentBranch.id !== branch.id) await this._switchBranch(branch.id);

    // Find update left from the target time, this is the update that needs to be executed to be up-to-date

    let leftUpdateID = null;

    for(let update of this.currentBranch.updates) {
      if(update.stepTime <= targetTime) leftUpdateID = update.stepID; // updates are sorted asc, take last one <=
      else break;
    }

    if(leftUpdateID == null) leftUpdateID = 0; // If no left update is found take the initial step of the branch to undo remaining updates

    await this._reachBranchStep(leftUpdateID);

    this.system.$emit("onHistoryTraversal", false);
  }

  async _traverseTo(branch, stepID) {
    this.system.$emit("onHistoryTraversal", true);

    if(this.currentBranch.id !== branch.id) await this._switchBranch(branch.id);

    await this._reachBranchStep(stepID);

    this.system.$emit("onHistoryTraversal", false);
  }

  async _reachBranchStep(stepID) {
    if (stepID === this.currentStepID) return;

    let undo = this.currentStepID > stepID;

    if (undo) {
      for (let up = this.currentBranch.updates.length - 1; up >= 0; up--) {
        let update = this.currentBranch.updates[up];

        if (update.stepID > this.currentStepID) continue; // Start at current step because we need to undo it
        else if (update.stepID <= stepID) break; // Do not undo target step because we want to reach that

        for (let uIdx = update.updateEvents.length - 1; uIdx >= 0; uIdx--) {
          if (update.updateEvents[uIdx].wasUndone === true) console.error("ALREADY UNDONE!!! when switching from " + this.currentStepID + " to " + stepID);
          update.updateEvents[uIdx].wasUndone = true;
          await update.updateEvents[uIdx].undo();
        }
      }
    } else {
      for (let up = 0; up <= this.currentBranch.updates.length - 1; up++) {
        let update = this.currentBranch.updates[up];

        if (update.stepID <= this.currentStepID) continue; // We start at currentStep + 1 because we are at currentStep
        else if (update.stepID > stepID) break; // Include target step because we want to redo that

        for (let uIdx in update.updateEvents) {
          if (update.updateEvents[uIdx].wasUndone !== true) console.error("ALREADY REDONE!!! when switching from " + this.currentStepID + " to " + stepID);
          update.updateEvents[uIdx].wasUndone = false;
          await update.updateEvents[uIdx].redo();
        }
      }
    }

    this.currentStepID = stepID;

    this._onPreviewChange();
  }

  async _switchBranch(branchID) {
    let path = this._findPathToBranch(branchID);

    for(let branch of path) {

      if(branch === this.currentBranch) continue;

      if(branch === this.currentBranch.parent) { // Branch is parent of current branch
        await this._reachBranchStep(-1);

        this.currentStepID = branch.getSplitStepForChild(this.currentBranch);
      } else { // Branch is child of current branch
        await this._reachBranchStep(this.currentBranch.getSplitStepForChild(branch))

        this.currentStepID = -1;
      }

      this.currentBranch = branch;
    }
  }

  _findPathToBranch(toBranchID) {
    if (this.currentBranch.id === toBranchID) return [];

    let queue = [[this.currentBranch]]
    let explored = new Set();

    while(queue.length > 0) {
      let path = queue.shift();
      let branch = path[path.length - 1];

      if(explored.has(branch.id)) continue;

      explored.add(branch.id);

      // Collect neighbours / parent

      let neighbours = [];

      for(let child of branch.children) neighbours.push(child);

      if(branch.parent != null) neighbours.push(branch.parent);

      for(let neighbour of neighbours) {
        let newPath = [...path]; // Copy
        newPath.push(neighbour);

        queue.push(newPath);

        if(neighbour.id === toBranchID) return newPath;
      }
    }
  }

  _onPreviewChange() {
    if(this.hasPreview()) this.editor.addClass("pipelineUpdatePreview");
    else this.editor.removeClass("pipelineUpdatePreview");
  }
}

export default {
  name: "HistoryGraph",
  props: ["traversalAllowed"],

  data() {
    return {
      opened: false,

      graphContainer: null,
      container: null,

      paddingX: 10,
      paddingY: 10,
      branchHeight: 0.75,
      splitLineWidth: 8,

      visualWidth: 0,
      visualHeight: 0,

      timeLineStart: -1,
      timeLineEnd: 0,

      currentBranchID: -1,
      currentStepID: -1,
      currentTargetStepID: -1, // Requested step from server
      currentTargetBranchID: -1,
      isWaitingForTarget: false,

      depthLevelLookup: {}, // Stores which depth is rendered at which level (to avoid gaps in depth values)

      branches: {},
      depthOccupation: new Map(), // Dict[depth, branch]
      pendingPipelineUpdates: [],

      updateViewer: new HistoryPipelineUpdateViewer(this),

      // Mouse control data
      wasDragged: false,
      isDragging: false,
      startX: 0,
      startY: 0,
      startClientX: 0,
      startClientY: 0,
      translateX: 0,
      translateY: 0,
      scale: 1,
      lastScale: 1,
      scrollDamping: 0.001,
      lastTimeLineMarkerPos: null,
    }
  },

  mounted() {
    this.graphContainer = document.getElementById("historyGraph");
    this.container = document.getElementById("historyGraphSVG");

    this.resizeObserver = new ResizeObserver(this._onResize);
    this.resizeObserver.observe(this.$el);

    this._onResize();

    makeGenericResizable($(this.$refs.container));

    let ths = this;

    // Listen for mouse movement outside our graph area, reset history preview in this case
    // This is a safer way than listening for mouseleave in case the browser misses the events (when tabbed out)

    $(document).on('mousemove', async function(event) {
      await synchronizeExecution(async () => {
        if(!ths._canInteractWithHistory() || !ths.updateViewer.hasPreview()) return;

        let bounds = ths.$refs.container.getBoundingClientRect();

        if(!(bounds.left <= event.clientX && event.clientX <= bounds.right &&
            bounds.top <= event.clientY && event.clientY <= bounds.bottom)) await ths.resetUpdateState();
      });
    });

    // Listen for mouse movement on the graph to show previews

    $(this.$el).on('mousemove', '.historyGraphBranchOv', async function(event){
      await synchronizeExecution(async () => {
        if(!ths._canInteractWithHistory() || !system.debuggerAllowHistoryPreview) return;

        let rct = event.currentTarget.getBoundingClientRect();
        let xPercentagePos = (event.clientX - rct.left) / rct.width;

        let branch = ths.branches[parseInt(event.target.getAttribute("branchID"))];
        if(branch == null) return;

        let targetTime = branch.timeRange() * xPercentagePos + branch.startTime;

        await ths._previewUpdateState(branch, targetTime);
      });
    });

    // Clicks on branch to switch

    $(this.$el).on('click', '.historyGraphBranchOv', async function(event){
      event.stopPropagation();

      if(ths.wasDragged) return;

      let branch = ths.branches[parseInt(event.target.getAttribute("branchID"))];
      if(branch == null) return;

      let rct = event.target.getBoundingClientRect();
      let xPercentagePos = (event.clientX - rct.left) / rct.width;
      let targetTime = branch.timeRange() * xPercentagePos + branch.startTime;

      await synchronizeExecution(async () => { await ths._onBranchClicked(branch.id, null, targetTime); });
    });

    // Click on split to switch to child

    $(this.$el).on('click', '.historyGraphSplitContainer', async function(event){
      event.stopPropagation();

      if(ths.wasDragged) return;

      await synchronizeExecution(async () => {await ths._onBranchClicked(parseInt(event.target.getAttribute("branchTo")), 0, null);});
    });

    // Click on update to switch to step

    $(this.$el).on('click', '.historyGraphPipelineUpdate', async function(event){
      event.stopPropagation();

      if(ths.wasDragged) return;

      await synchronizeExecution(async () => {await ths._onBranchClicked(parseInt(event.target.getAttribute("branchID")), parseInt(event.target.getAttribute("stepID")), null);});
    });

    $(document).keyup(async function(e) {
      await synchronizeExecution(async () => { await ths.resetUpdateState();});

      if(e.key === "Escape") ths.close();
    });
  },

  beforeDestroy() {
    this.resizeObserver.unobserve(this.$el);
  },

  computed: {
    isOpen: function() {
      return this.opened;
    }
  },

  methods: {
    open() {
      this.opened = true;

      // Resets all data to trigger updating of the missed UI changes during close
      for(let branch in this.branches) {
        let b = this.branches[branch];
        if(b.hasChangedData) b.updateData(this, b.startTime, b.endTime, b.stepCount, b.stepOffset);
      }

      this._resetViewport();
    },

    close() {
      this.opened = false;
    },

    reset() {
      this.timeLineStart = -1;
      this.timeLineEnd = 0;
      this.currentStepID = -1;
      this.currentBranchID = -1;
      this.currentTargetStepID = - 1;
      this.currentTargetBranchID = -1;
      this.isWaitingForTarget = false;

      for(let branch in this.branches) this.branches[branch].destroy();

      this.branches = {};
      this.depthLevelLookup = {};
      this.depthOccupation.clear();
      this.pendingPipelineUpdates = [];

      this.close();
    },

    async setCurrentStep(branchID, stepID, stepTime, register) {
      let newBranch = this._switchBranch(branchID, stepTime);

      this.currentStepID = stepID;

      if(this.isWaitingForTarget) {
        this.isWaitingForTarget = this.currentStepID !== this.currentTargetStepID || this.currentBranchID !== this.currentTargetBranchID;

        // Just in case requested targetStep gets lost and we are in a deadlock
        if(register && this.currentTargetStepID == null && this.isWaitingForTarget) this.isWaitingForTarget = false;
      }

      await this._setUpdateState(newBranch, stepID, register);
    },

    updateBranchData(branchID, branchStartTime, branchEndTime, stepCount, stepOffset, deleteOnEmpty=false) {
      this._updateBranch(branchID, branchStartTime, branchEndTime, stepCount, stepOffset, true);

      if(stepCount === 0 && deleteOnEmpty) this._removeBranch(branchID); // TODO: REMOVE PU WHEN STEP ARE UPDATED
    },

    onBranchSplit(branchID, parentID, splitTime, splitStep) {
      this._splitBranch(branchID, parentID, splitTime, splitStep);
    },

    signalTargetRequested(targetBranchID, targetStepID) {
      // Called when the traversal to a specific branch/step/time is requested from the server

      this.currentTargetStepID = targetStepID; // Might be null, in this case we are not sure about the correct step and request it from server
      this.currentTargetBranchID = targetBranchID;

      this.isWaitingForTarget = this.currentStepID !== targetStepID || targetBranchID !== this.currentBranchID;

      // Only signal the new branch, step and time will be sent from server
      if(this.currentBranchID !== targetBranchID) this._switchBranch(targetBranchID, null);
    },

    onReceiveRequestedStep(branchID, stepID) {
      let branch = this.branches[branchID];

      if(!this._canInteractWithHistory(false) || branch == null) {
        // In case we are not able to request the step we need to reset our state to the current branch/step
        this._switchBranch(this.currentBranchID);
        this.signalTargetRequested(this.currentBranchID, this.currentStepID);

        return;
      }

      this.signalTargetRequested(branchID, stepID);

      this.$emit("onBranchTraversal", branchID, stepID, null, branch.stepCount);
    },

    getCurrentDeltaTime(currentTime) {
      return Math.max(0, this.timeLineEnd - currentTime);
    },

    getStepOffsetForBranch(branchID) {
      let branch = this.branches[branchID];
      if(branch == null) return 0;

      return branch.stepOffset;
    },

    _onResize() {
      if(!this.opened) return;

      // Center the container relative to the parent debugging area
      let container = this.$refs.container.getBoundingClientRect();
      let parent = this.$refs.container.parentElement.getBoundingClientRect();

      this.$refs.container.style.left = -(container.width - parent.width) / 2 + "px";

      this._onRescaleGraph();
    },

    _onRescaleGraph() {
      let graph = this.$refs.svg.getBoundingClientRect();
      this.visualWidth = graph.width;
      this.visualHeight = graph.height;

      this._updateXPositions(false);
      this._updateYPositions(false);
      this._updateSplits();
      this._updateTimeLine();
    },

    // ---------------------------------- Updates ----------------------------------

    assignPipelineUpdates(branchID, stepID, stepTime, updateIDs) {
      // Assigns previously registered pending updates to the correct branch/step

      let branch = this.branches[branchID];
      if(branch == null) return;

      let updates = [];
      let remaining = [];

      for(let up of this.pendingPipelineUpdates) {
        if(updateIDs.includes(up.updateID)) updates.push(up);
        else remaining.push(up);
      }

      branch.registerUpdates(stepID, stepTime, updates);

      this.pendingPipelineUpdates = remaining;
    },

    registerPipelineUpdateEvent(event) {
      this.pendingPipelineUpdates.push(event);
    },

    async undoPendingUpdateEvents(updateIDs) {
      this.$emit("onHistoryTraversal", true);

      // Undo in reverse order
      let remaining = [];

      for (let uIdx = this.pendingPipelineUpdates.length - 1; uIdx >= 0; uIdx--) {
        let up = this.pendingPipelineUpdates[uIdx];

        if(updateIDs.includes(up.updateID)) await up.undo();
        else remaining.push(up);
      }

      this.$emit("onHistoryTraversal", false);

      this.pendingPipelineUpdates = remaining;
    },

    async _setUpdateState(newBranch, stepID, register) {
      await this.updateViewer.setCurrentState(newBranch, stepID, register);
    },

    async _previewUpdateState(branch, targetTime) {
      await this.updateViewer.showPreview(branch, targetTime);
    },

    async resetUpdateState() {
      await this.updateViewer.reset();
    },

    // ---------------------------------- Timeline ----------------------------------

    _updateTimeLine() {
      if(!this.opened) return;

      const rect = this.$refs.content.getBoundingClientRect();

      if(rect.width === 0) return;

      let maxWidth = rect.width * this.scale;

      let currentTimeRange = this.timeLineEnd - this.timeLineStart;
      let visibleTimeRange = currentTimeRange / this.scale;

      let startTime = this.timeLineStart + Math.abs((this.translateX / maxWidth) * currentTimeRange);
      let endVal = this.timeLineEnd - startTime - visibleTimeRange;

      this.$refs.tlLeftText.textContent = "ΔTime: " + formatTime(this.timeLineEnd - startTime);
      this.$refs.tlRightText.textContent = "ΔTime: " + (endVal >= 0.01 ? "" : "") + formatTime(endVal);
    },

    _updateTimeLineMarker(mousePos) {
      this.lastTimeLineMarkerPos = mousePos;

      if(mousePos == null) {
        this.$refs.timelineMarker.style.height = "0px";
        this.$refs.tlCenterText.textContent = "";
      } else {
        const rect = this.$refs.content.getBoundingClientRect();

        let viewportPos = mousePos - rect.left;

        let maxWidth = rect.width * this.scale;
        let currentTimeRange = this.timeLineEnd - this.timeLineStart;
        let visibleTimeRange = currentTimeRange / this.scale;

        let startTime = this.timeLineStart + Math.abs((this.translateX / maxWidth) * currentTimeRange);
        let endVal = this.timeLineEnd - startTime - visibleTimeRange;

        let leftVal = this.timeLineEnd - startTime;

        let timeVal = leftVal + (endVal - leftVal) * viewportPos / rect.width;

        let marker = this.$refs.timelineMarker;

        marker.style.height = (this.visualHeight + this.paddingY * 2) + "px";
        marker.style.left = viewportPos + "px";

        this.$refs.tlCenterText.textContent = "ΔTime: " + (timeVal >= 0.01 ? "" : "") + formatTime(timeVal);
      }
    },

    // ----------------------------- Branch Calculations -----------------------------

    _switchBranch(branchID, stepTime = null) {
      if(this.currentBranchID !== branchID) {
        let oldBranch = this.branches[this.currentBranchID];
        if(oldBranch != null) oldBranch.markCurrentState(false, 0);
      }

      let newBranch = this.branches[branchID];
      if(newBranch != null && stepTime != null) newBranch.markCurrentState(true, stepTime);

      this.currentBranchID = branchID;

      return newBranch;
    },

    async _onBranchClicked(branchID, targetStep, targetTime) {
      // Depending if we clicked on a fixed step (update, split) or on the branch itself, targetStep or targetTime is null
      if(!this._canInteractWithHistory()) return;

      let branch = this.branches[branchID];
      if(branch == null) return;

      await this.resetUpdateState();

      this.signalTargetRequested(branchID, targetStep);

      this.$emit("onBranchTraversal", branchID, targetStep, targetTime, branch.stepCount);
    },

    _canInteractWithHistory(includeWaiting = true) {
      return this.traversalAllowed && (!includeWaiting || !this.isWaitingForTarget) && this.pendingPipelineUpdates.length === 0;
    },

    _updateXPositions(updateSplits=true) {
      for(let b in this.branches) this.branches[b].updateXPosition(this, updateSplits);
    },

    _updateYPositions(updateSplits=true) {
      for(let b in this.branches) this.branches[b].updateYPosition(this, updateSplits);
    },

    _updateSplits() {
      for(let b in this.branches) this.branches[b].updateSplitPositions(this);
    },

    _updateGraphDepths(update=true) {
      let ordered = Array.from(this.depthOccupation.keys());

      this.depthLevelLookup = {};

      for(let orderID in ordered) this.depthLevelLookup[ordered[orderID]] = orderID;

      if(update) this._updateYPositions();
    },

    _updateGraphTime(update=true) {
      let currentStartTime = -1;
      let currentEndTime = 0;

      for(let v of Object.values(this.branches)) {
        if(currentStartTime === -1 || v.startTime < currentStartTime) currentStartTime = v.startTime;

        if(v.endTime > currentEndTime) currentEndTime = v.endTime;
      }

      // Check if the time value has changed, this requires an update
      let changedTime = this.timeLineStart !== currentStartTime || this.timeLineEnd !== currentEndTime;

      this.timeLineStart = currentStartTime;
      this.timeLineEnd = currentEndTime;

      if(!update) return;

      if(changedTime) {
        this._updateXPositions();
        this._updateTimeLine();

        if(this.lastTimeLineMarkerPos != null) this._updateTimeLineMarker(this.lastTimeLineMarkerPos);
      }
    },

    _splitBranch(newID, sourceBranchID, splitTime, splitStep) {
      let sb = this.branches[sourceBranchID];
      if(sb == null) return;

      if(this.branches[newID] != null) console.error("Branch to split already exists! [ID " + newID + "]");

      let newBranch = this._createBranch(newID, sb, splitTime, splitTime, 0);
      this._createSplitLine(sb, newBranch, splitStep, splitTime);

      sb.registerChild(newBranch);
    },

    _removeDepthOccupation(branch, updateDepths=true) {
      let doc = this.depthOccupation.get(branch.depth);

      if(doc != null) {
        let idx = doc.indexOf(branch);

        if(idx > -1) {
          doc.splice(idx, 1);

          if(doc.length === 0) {
            this.depthOccupation.delete(branch.depth);
            this._updateGraphDepths(updateDepths);
          }
        } // else might occur during initial create branch
      }
    },

    _findEmptyDepth(targetDepth, branch, updateDepths=true) {
      if(branch.depth !== targetDepth) this._removeDepthOccupation(branch, updateDepths); // Clear prev occupation

      let depthFound = false;
      let existingEntry = false;

      while(!depthFound) {
        depthFound = true;

        let doc = this.depthOccupation.get(targetDepth);

        // If depth is completely empty, register and return depth

        if(doc == null) {
          this.depthOccupation.set(targetDepth, [branch]);

          this._updateGraphDepths(updateDepths);

          return targetDepth;
        }

        // Otherwise search all existing entries
        existingEntry = doc.indexOf(branch) > -1;

        for(let id in doc) {
          let other = doc[id];

          if(other === branch) continue;

          if(branch.startTime <= other.startTime && branch.endTime >= other.startTime
            || branch.startTime <= other.endTime && branch.endTime >= other.endTime
            || branch.startTime >= other.startTime && branch.endTime <= other.endTime) {
            // Occupied, try next depth
            targetDepth++;
            depthFound = false;

            // Remove existing entry since we left the current depth
            if(existingEntry) this._removeDepthOccupation(branch, updateDepths);

            break;
          }
        }

        // No occupier found, take this depth and register

        if(depthFound) {
          if(!existingEntry) doc.push(branch);

          return targetDepth;
        }
      }
    },

    _createBranch(id, parent, startTime, endTime, stepCount, stepOffset) {
      let line = this._createLine(0, 0, 0, 0, 0);
      line.setAttribute("class", "historyGraphBranch");

      let branchContainer = document.createElement('div');
      branchContainer.style.position = "absolute";
      branchContainer.setAttribute("class", "historyGraphBranchOv");
      branchContainer.setAttribute("branchID", id);

      this.container.appendChild(line);
      this.graphContainer.prepend(branchContainer);

      let branch = new HistoryBranch(id, 0, parent, startTime, endTime, stepCount, stepOffset, line, branchContainer);

      branch.depth = this._findEmptyDepth(parent != null ? parent.depth + 1 : 0, branch);

      this._updateGraphTime();

      branch.updateXPosition(this);
      branch.updateYPosition(this);

      this.branches[id] = branch;

      return branch;
    },

    _createSplitLine(branchFrom, branchTo, splitStep, splitTime) {
      let line = this._createPath(0, 0, 0, 0, this.splitLineWidth);
      line.setAttribute("class", "historyGraphSplitLine");
      this.container.prepend(line);

      let lineContainer = document.createElement('div');
      lineContainer.style.position = "absolute";
      lineContainer.setAttribute("class", "historyGraphSplitContainer");
      lineContainer.setAttribute("branchFrom", branchFrom.id);
      lineContainer.setAttribute("branchTo", branchTo.id);
      this.graphContainer.appendChild(lineContainer);

      let sp = new HistorySplit(branchFrom, branchTo, splitStep, splitTime, line, lineContainer);
      sp.updatePosition(this.splitLineWidth);

      branchFrom.registerSplit(sp);
    },

    _updateBranch(id, startTime, endTime, stepCount, stepOffset, createIfNone) {
      let branch = this.branches[id];

      if(branch == null) {
        if(createIfNone) this._createBranch(id, null, startTime, endTime, stepCount, stepOffset);
      } else branch.updateData(this, startTime, endTime, stepCount, stepOffset);
    },

    _removeBranch(branchID) {
      let branch = this.branches[branchID];

      if(branch == null) return;

      this._removeDepthOccupation(branch, false);

      branch.destroy();
      delete this.branches[branch.id];

      this._updateGraphDepths(false);
      this._updateGraphTime(false);

      this._updateXPositions();
      this._updateYPositions();
    },

    _timeToXPos(time) {
      let range = this.timeLineEnd - this.timeLineStart;

      if(range <= 0) return 0;

      return Math.max(0, time - this.timeLineStart) / range;
    },

    _createLine(fromX, toX, fromY, toY, strokeWidth) {
      let p = document.createElementNS("http://www.w3.org/2000/svg", "line");
      p.setAttribute("x1", "" + fromX);
      p.setAttribute("y1", "" + fromY);
      p.setAttribute("x2", "" + toX);
      p.setAttribute("y2", "" + toY);
      p.setAttribute("stroke-width", "" + strokeWidth);
      //p.setAttribute("stroke-linecap", "round");

      return p;
    },

    _createPath(fromX, toX, fromY, toY, strokeWidth) {
      let p = document.createElementNS("http://www.w3.org/2000/svg", "path");
      p.setAttribute("d", "");
      p.setAttribute("stroke-width", "" + strokeWidth);

      return p;
    },

    // ------------------------------- Viewport Control -------------------------------

    _onMouseDown(e) {
      e.preventDefault();
      e.stopPropagation();

      this.wasDragged = false;
      this.isDragging = true;
      this.startX = e.clientX - this.translateX;
      this.startY = e.clientY - this.translateY;
      this.startClientX = e.clientX;
      this.startClientY = e.clientY;
    },

    _onMouseMove(e) {
      if (this.isDragging) {
        e.preventDefault();
        e.stopPropagation();

        this.translateX = e.clientX - this.startX;
        this.translateY = e.clientY - this.startY;
        this._updateTransform();
      }

      this._updateTimeLineMarker(e.clientX);
    },

    _onMouseUp(e) {
      if(this.isDragging) {
        e.preventDefault();
        e.stopPropagation();
        this.wasDragged = distance(this.startClientX, this.startClientY, e.clientX, e.clientY) > 10;
      } else this.wasDragged = false;

      this.isDragging = false;
    },

    _onMouseLeave() {
      this.isDragging = false;
      this.wasDragged = false;
      this._updateTimeLineMarker(null);
    },

    _resetViewport() {
      this.scale = 1;
      this.translateX = 0;
      this.translateY = 0;
      this._updateTransform();
    },

    _clampTranslation() {
      // Force translation so that the visible area is always inside the rect
      const rect = this.$refs.content.getBoundingClientRect();

      this.translateX = Math.min(0, this.translateX);
      this.translateY = Math.min(0, this.translateY);

      this.translateX = Math.max(-(rect.width * this.scale - rect.width), this.translateX);
      this.translateY = Math.max(-(rect.height * this.scale - rect.height), this.translateY);
    },

    _onMouseScroll(e) {
      const rect = this.$refs.content.getBoundingClientRect();

      // Mouse position relative to outer div

      let mouseX = e.clientX - rect.left;
      let mouseY = e.clientY - rect.top ;

      // The target point inside the inner div which we are focusing (taking into account translations)

      let targetX = mouseX - this.translateX;
      let targetY = mouseY - this.translateY;

      let oldScale = this.scale;

      // Apply new scale

      // Scroll value is always a fix percentage of the current scroll value
      let scrollFac = this.scale * this.scrollDamping;
      this.scale += e.deltaY * -scrollFac;
      this.scale = Math.max(this.scale, 1);

      // The new target positions is the old position with the new correct scale

      let newTargetX = targetX * this.scale / oldScale;
      let newTargetY = targetY * this.scale / oldScale;

      // The required translation is the difference between the cursor position and new desired position

      this.translateX = mouseX - newTargetX;
      this.translateY = mouseY - newTargetY;

      this._updateTransform();
    },

    _updateTransform() {
      if(!this.opened) return;

      this._clampTranslation();
      this._updateTimeLine();

      this.$refs.graph.style.transform = `translate(${this.translateX}px, ${this.translateY}px)`; // Execution: right to left // scale(${this.scale})

      // Css scale does not work correctly with the increase in visualWidth ... so scale manually
      this.$refs.graph.style.width = this.scale * 100 + "%";
      this.$refs.graph.style.height = this.scale * 100 + "%";


      if(this.lastScale !== this.scale) this._onRescaleGraph();
      this.lastScale = this.scale;
    }
    },
}

</script>

<style scoped>

#historyGraphContainer {
  overflow: hidden;
  margin-top: -2px;
  position: relative;
  z-index: 1;
  width: 100%;
  height: 200px;
  min-width: 100%;
  min-height: 200px;
  border: 2px solid #dedede;
  background: rgba(247, 247, 247, 0.9);
  border-bottom-left-radius: 6px;
  border-bottom-right-radius: 6px;
}

#historyGraph {
  width: 100%;
  height: 100%;
  position: relative;

  transform-origin: 0 0;
}

#historyGraphSVG {
  height: 100%;
  width: 100%;
}

#historyTimeline {
  width: 100%;
  height: 30px;
  margin: 0 auto;
  background: rgba(247, 247, 247, 1);
  position: relative;
}

.historyTl {
  background: #444;
  width: 100%;
  height: 5px;
  margin-top: 5px;
  position: absolute;
}

.historyTlBorder {
  height: 200%;
  width: 2px;
  position: absolute;
  background: #444;
  top: -50%;
}

.historyTlText {
  position: absolute;
  font-size: 14px;
  top: 100%;
  cursor: default;
}

#historyTimelineMarker {
  position: absolute;
  width: 1px;
  background: #dedede;
  height: 100%;
  bottom: 0;
  left: 0;
  pointer-events: None;
}

</style>

<style>

.historyGraphSplitLine {
  stroke: #d0d0d0;
  fill: none;
}

.historyGraphBranch {
  stroke: #444;
}

.historyGraphCurrentBranch {
  stroke: #c2d6f6;
}

.historyGraphCurrentProgress {
  pointer-events: none;
  background: #92b6f0;
  position: absolute;
  height: 100%;
  left: 0;
  top: 0;
}

.historyGraphBranchOv {
  cursor: pointer;

  border: 2px solid #888;
  box-sizing: border-box;
}

.historyGraphSplitContainer {
  box-sizing: border-box;
  border: 2px solid #888;
  background: rgb(90, 90, 90);
  cursor: pointer;
}

.historyGraphButton {
  cursor:pointer;

  border-radius: 6px;
  background: #444;
  color:white;
  height:20px;
  width: 50px;

  position:absolute;

  -webkit-touch-callout: none; /* iOS Safari */
  -webkit-user-select: none; /* Safari */
  -moz-user-select: none; /* Old versions of Firefox */
  -ms-user-select: none; /* Internet Explorer/Edge */
  user-select: none; /* Non-prefixed version, currently supported by Chrome, Edge, Opera and Firefox */
}

.historyGraphPipelineUpdate {
  cursor: pointer;
  background: white;
  position: absolute;
  height: 100%;
  left: 0;
  top: 0;
  width: 3px;
}

.pipelineUpdatePreview {
  opacity: 0.667;
}

</style>
