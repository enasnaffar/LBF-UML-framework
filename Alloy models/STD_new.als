module STD_new

// ------------------ Core Meta Classes ------------------

sig StateMachine {
    states: set State,
    transitions: set Transition
}

// Each State and Transition belongs to exactly one StateMachine
sig State {
    machine: one StateMachine,
    incoming: set Transition,
    outgoing: set Transition
}

sig Transition {
    machine: one StateMachine,
    source: one State,
    target: one State,
    triggers: set Trigger,
    guard: lone Guard
}

// ------------------ Trigger and Guard ------------------

sig Trigger {
    transition: one Transition,
    event: one Event
}

sig Guard {
    transition: one Transition
}

// ------------------ Event Types ------------------

abstract sig Event {}

sig TimeEvent extends Event {}
sig SignalEvent extends Event {}
sig ChangeEvent extends Event {}
sig MessageEvent extends Event {}

// ------------------ Constraints ------------------

// OPTION A IMPLEMENTED:
// A StateMachine is valid if:
//   • it is COMPLETELY empty  (no states AND no transitions)
//   • OR it is FULLY defined (at least one state AND at least one transition)
//   • partial definitions are not allowed.
fact StateMachineCardinality {
    all sm: StateMachine |
        (no sm.states and no sm.transitions) or
        (some sm.states and some sm.transitions)
}

// States belong to exactly one StateMachine
fact StateMachineAssociation {
    all s: State | one s.machine
}

// Transitions belong to exactly one StateMachine
fact TransitionAssociation {
    all t: Transition | one t.machine
}

// Transition source and target must be single states
fact TransitionSourceTarget {
    all t: Transition |
        one t.source and one t.target
}

// States relate to 0 or more transitions
fact StateTransitionRelation {
    all s: State |
        s.incoming in Transition and
        s.outgoing in Transition
}

// Transition may have 0 or more triggers, and at most one guard
fact TransitionTriggerGuard {
    all t: Transition |
        lone t.guard and
        t.triggers in Trigger
}

// Trigger must have exactly one Event
fact TriggerEventRelation {
    all tr: Trigger |
        one tr.event
}

// Transition must appear in its source.outgoing and target.incoming
fact TransitionStateConsistency {
    all t: Transition | {
        t in t.source.outgoing
        t in t.target.incoming
    }
}
