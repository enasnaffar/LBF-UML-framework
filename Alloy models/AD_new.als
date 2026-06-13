module AD_new

// ------------------ Core Meta Classes ------------------

sig Activity {
    nodes: set Node,
    edges: set ActivityEdge
}

// Every Node has incoming/outgoing edges
abstract sig Node {
    activity: lone Activity,
    incoming: set ActivityEdge,
    outgoing: set ActivityEdge
}

sig ActivityEdge {
    activity: lone Activity,
    source: one Node,
    target: one Node
}

// ------------------ Node Specializations ------------------

sig ActivityNode extends Node {}

abstract sig ControlNode extends Node {}

// ---- Control Nodes (UPDATED) ----
one sig InitialNode extends ControlNode {}
sig FinalNode extends ControlNode {}
sig MergeNode extends ControlNode {}
sig DecisionNode extends ControlNode {}

// ---- Edge Kinds (unchanged) ----
sig ObjectFlow extends ActivityEdge {}
sig ControlFlow extends ActivityEdge {}


// ------------------ Corrected Constraints ------------------

// Containment consistency
fact ActivityContainment {
    all a: Activity | {
        a.nodes.activity = a
        a.edges.activity = a
    }
}

// Node-edge connection consistency
fact NodeEdgeRelations {

    // Edges must connect nodes in the same Activity
    all e: ActivityEdge | {
        e.source.activity = e.activity
        e.target.activity = e.activity
    }

    // Define incoming/outgoing sets automatically
    all n: Node | {
        n.incoming = { e: ActivityEdge | e.target = n }
        n.outgoing = { e: ActivityEdge | e.source = n }
    }
}

// Exactly one InitialNode per Activity
fact ActivityInitialNode {
    all a: Activity |
        one n: InitialNode | n in a.nodes
}

// At least one FinalNode per Activity
fact ActivityFinalNode {
    all a: Activity |
        some n: FinalNode | n in a.nodes
}

// ------------------ Control Node Semantics ------------------

// InitialNode: 0 incoming, exactly 1 outgoing
fact InitialNodeEdges {
    all n: InitialNode | {
        no n.incoming
        one n.outgoing
    }
}

// FinalNode: ≥1 incoming, 0 outgoing
fact FinalNodeEdges {
    all n: FinalNode | {
        some n.incoming
        no n.outgoing
    }
}

// MergeNode: ≥2 incoming, exactly 1 outgoing
fact MergeNodeEdges {
    all n: MergeNode | {
        #n.incoming >= 2
        one n.outgoing
    }
}

// DecisionNode: exactly 1 incoming, ≥2 outgoing
fact DecisionNodeEdges {
    all n: DecisionNode | {
        one n.incoming
        #n.outgoing >= 2
    }
}

// ------------------ Global Safety Constraints ------------------

// No direct Initial → Final control flow
fact NoDirectInitialToFinal {
    all e: ControlFlow |
        not (e.source in InitialNode and e.target in FinalNode)
}

// No self loops
fact NoSelfLoop {
    all e: ActivityEdge | e.source != e.target
}
