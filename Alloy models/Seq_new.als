module seq_new
open uc_new
// =========================
// Interaction
// =========================
sig Interaction {
    lifelines: set Lifeline,
    messages: set Message,
    fragments: set InteractionFragment,
    refs: set InteractionUse
}

// =========================
// Lifeline
// =========================
sig Lifeline {
    sentMessages: set Message,
    receivedMessages: set Message,
    represents: lone ObjectTag

}

// =========================
// Message
// =========================
sig Message {
    sender: one Lifeline,
    receiver: one Lifeline,
    sort: one MessageSort,
    order: one MessageOrder
}

sig MessageOrder {}
enum MessageSort { SYNCHRONOUS, ASYNCHRONOUS }


// =========================
// InteractionFragment
// =========================
abstract sig InteractionFragment {
    covered: set Lifeline
}


// ======================================================
// CombinedFragment (NO SUBTYPES ANYMORE)
// ======================================================
sig CombinedFragment extends InteractionFragment {
    operands: set InteractionOperand
}


// ======================================================
// InteractionUse
// ======================================================
sig InteractionUse extends InteractionFragment {
    refersTo: one Interaction
}


// ======================================================
// Interaction Operand + Guard
// ======================================================

// NEW ENUMERATION:
enum OperandKind { LOOP, OPT, PAR, BREAK, ALT }

sig InteractionOperand {
    guards: set SGuard,
    kind: one OperandKind    // NEW ATTRIBUTE
}

sig SGuard {}


// =========================
// Facts
// =========================
fact LifelineMessageConsistency {
    all m: Message | 
        m in m.sender.sentMessages and m in m.receiver.receivedMessages
}

fact MessageOrderConsistency {
    all m: Message | one m.order
}

fact CombinedFragmentHasOperands {
    all cf: CombinedFragment | cf.operands != none
}

fact OperandBelongsToFragment {
    all op: InteractionOperand | some cf: CombinedFragment | op in cf.operands
}

fact GuardConsistency {
    all op: InteractionOperand | op.guards in SGuard
}

