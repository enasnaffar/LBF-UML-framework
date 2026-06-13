module cross

open uc_new
open cd_new
open seq_new
open ad_new
open std_new
open amapping

// =====================================================
// 1. UseCase ↔ Interaction (Sequence Diagram) Mapping
// =====================================================

sig UseCaseInteractionMapping {
    usecase: one UseCase,        
    interaction: one Interaction 
}

fact UseCaseInteractionMappingUnique {
    all disj m1, m2: UseCaseInteractionMapping |
        m1.usecase != m2.usecase and m1.interaction != m2.interaction
}


// =====================================================
// 2. UseCase ↔ Activity (Activity Diagram) Mapping
// =====================================================

sig UseCaseActivityMapping {
    usecase: one UseCase,   
    activity: one Activity  
}

fact UseCaseActivityMappingUnique {
    all disj m1, m2: UseCaseActivityMapping |
        m1.usecase != m2.usecase and m1.activity != m2.activity
}


// =====================================================
// 3. Message → Operation Mapping
// =====================================================

sig MessageOperationMapping {
    msg: one Message,
    op: one Operation
}

fact MessageOperationMappingUnique {
    all m1, m2: MessageOperationMapping |
        m1.msg = m2.msg implies m1 = m2
}


// =====================================================
// 4. Trigger → Message Mapping + Local Ordering
// =====================================================

sig TriggerMessageMapping {
    trig: one UTrigger,
    msg: one Message
}

fact TriggerMessageUnique {
    all m1, m2: TriggerMessageMapping |
        m1.trig = m2.trig implies m1 = m2
}

sig NextMessage {
    pre: one Message,
    suc: one Message
}


// =====================================================
// 5. Cross-Model Consistency Rules (EXISTING)
// =====================================================

fact ObjectInSequenceConsistency {
    all uc: UseCase, o: ObjectTag |
        o in uc.textualDesc.objectTags implies
            some uim: UseCaseInteractionMapping, lif: Lifeline |
                uim.usecase = uc and
                lif in uim.interaction.lifelines and
                lif.represents = o
}

fact TriggerIsFirstMessage {
    all uim: UseCaseInteractionMapping |
        all tm: TriggerMessageMapping |
            tm.trig in uim.usecase.textualDesc.triggers implies {
                tm.msg in uim.interaction.messages
                no nm: NextMessage |
                    nm.suc = tm.msg and nm.pre in uim.interaction.messages
            }
}

fact AlternativeFlowRequiresDecisionNode {
    all ua: UseCaseActivityMapping |
        (some ua.usecase.textualDesc.alternativeFlow) implies
            some dn: DecisionNode | dn in ua.activity.nodes
}

fact IncludeHasRefFrame {
    all inc: Include |
        some uimBase, uimInc: UseCaseInteractionMapping |
            uimBase.usecase = inc.source and
            uimInc.usecase = inc.target implies {
                some iu: InteractionUse |
                    iu in uimBase.interaction.refs and
                    iu.refersTo = uimInc.interaction
            }
}

fact ExtendHasOptAltBreakRefFrame {
    all ext: Extend |
        some uimBase, uimExt: UseCaseInteractionMapping |
            uimBase.usecase = ext.source and
            uimExt.usecase  = ext.target implies {

                some cf: CombinedFragment |
                    cf in uimBase.interaction.fragments and
                    some op: InteractionOperand |
                        op in cf.operands and
                        (op.kind = OPT or op.kind = ALT or op.kind = BREAK)

                some iu: InteractionUse |
                    iu in uimBase.interaction.refs and
                    iu.refersTo = uimExt.interaction
            }
}


// =====================================================
// 6. ObjectTag ↔ Class ↔ Lifeline Consistency
// =====================================================

fact AllObjectTagsMapped {
    all ot: ObjectTag | one m: ObjectTagClassMapping | m.tag1 = ot
}

fact ObjectTagsAppearAsLifelines {
    all m: UseCaseInteractionMapping |
        let uc  = m.usecase,
            td  = uc.textualDesc,
            inter = m.interaction |
        all ot: td.objectTags |
            some lf: inter.lifelines | lf.represents = ot
}


// =====================================================
// 7. NEW RULE: UseCase Trigger ↔ StateMachine Event
// =====================================================
//
// Semantics:
// - If a UseCase has NO trigger → rule does NOT apply
// - If the related Class has NO StateMachine → rule does NOT apply
// - Otherwise → the trigger must correspond to an SM event
//

fact UC_SM_TriggerConsistency {

    all uim: UseCaseInteractionMapping |
    let uc = uim.usecase |

        (no uc.textualDesc.triggers)

        or

        (all ut: uc.textualDesc.triggers |

            some tm: TriggerMessageMapping |

                tm.trig = ut and
                tm.msg in uim.interaction.messages

                and

                (
                    no mo: MessageOperationMapping |
                        mo.msg = tm.msg and
                        some ocm: OperationClassMapping |
                            ocm.op = mo.op and
                            some csm: ClassStateMachineMapping |
                                csm.cls = ocm.cls
                )

                or

                (
                    some mo: MessageOperationMapping |
                        mo.msg = tm.msg and
                        some ocm: OperationClassMapping |
                            ocm.op = mo.op and
                            some csm: ClassStateMachineMapping |
                                csm.cls = ocm.cls and
                                some mev: MessageEventMapping |
                                    mev.msg = tm.msg and
                                    some t: csm.sm.transitions |
                                        some tr: t.triggers |
                                            tr.event = mev.ev
                )
        )
}

// =====================================================
// 8. Assertions (UNCHANGED)
// =====================================================

assert AllMessagesHaveOperations {
    all m: Message |
        some mo: MessageOperationMapping | mo.msg = m
}

assert AllUseCasesHaveActivities {
    all uc: UseCase |
        some ua: UseCaseActivityMapping | ua.usecase = uc
}

assert AllUseCasesHaveInteractions {
    all uc: UseCase |
        some ui: UseCaseInteractionMapping | ui.usecase = uc
}

assert UniqueUseCaseActivityMapping {
    all disj m1, m2: UseCaseActivityMapping |
        m1.usecase != m2.usecase and m1.activity != m2.activity
}

assert UniqueUseCaseInteractionMapping {
    all disj m1, m2: UseCaseInteractionMapping |
        m1.usecase != m2.usecase and m1.interaction != m2.interaction
}
