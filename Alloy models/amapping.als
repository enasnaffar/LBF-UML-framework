module amapping

open uc_new
open cd_new
open seq_new
open std_new

// =====================================================
// Existing: ObjectTag ↔ Class mapping
// =====================================================

sig ObjectTagClassMapping {
    tag1: one ObjectTag,
    cls1: one Class_
}

fact AllObjectTagsMapped {
    all ot: ObjectTag | one m: ObjectTagClassMapping | m.tag1 = ot
}


// =====================================================
// NEW: Operation ↔ Class mapping
// =====================================================

sig OperationClassMapping {
    op: one Operation,
    cls: one Class_
}

fact OperationClassMappingUnique {
    all m1, m2: OperationClassMapping |
        m1.op = m2.op implies m1 = m2
}


// =====================================================
// NEW: Class ↔ StateMachine mapping
// =====================================================

sig ClassStateMachineMapping {
    cls: one Class_,
    sm:  one StateMachine
}

fact ClassStateMachineMappingUnique {
    all m1, m2: ClassStateMachineMapping |
        m1.cls = m2.cls implies m1 = m2
}


// =====================================================
// NEW: Message ↔ Event mapping
// =====================================================

sig MessageEventMapping {
    msg: one Message,
    ev:  one Event
}

fact MessageEventMappingUnique {
    all m1, m2: MessageEventMapping |
        m1.msg = m2.msg implies m1 = m2
}
