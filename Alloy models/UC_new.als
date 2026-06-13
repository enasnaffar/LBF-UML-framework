// Module declaration
module UC_new

//======================================================
// USE CASE MODEL ELEMENTS
//======================================================

sig UseCase {
textualDesc: one TextualDescription,
extensionPoints: set ExtensionPoint
}

sig Actor {}

abstract sig URelationship {}

sig Association extends URelationship {
useCaseEnd: one UseCase,
actorEnd: one Actor
}

abstract sig DirectedRelationship extends URelationship {
source: one UseCase,
target: one UseCase
}

sig Generalization extends DirectedRelationship {}

sig Include extends DirectedRelationship {
ownerFlow: one BasicFlow
}

sig Extend extends DirectedRelationship {
ownerAltFlow: one AlternativeFlow,
extensionPoint: one ExtensionPoint
}

sig ExtensionPoint {}

//======================================================
// TEXTUAL DESCRIPTION ELEMENTS
//======================================================

sig TextualDescription {
basicFlow: one BasicFlow,
alternativeFlow: set AlternativeFlow,
triggers: some UTrigger,
preconditions: some Precondition,
postconditions: some Postcondition,
objectTags: some ObjectTag
}

sig ObjectTag {}

sig UTrigger {}

sig Precondition {}

sig Postcondition {}

//======================================================
// FLOW OF EVENTS
//======================================================

abstract sig FlowOfEvents {
steps_: some Step
}

sig BasicFlow extends FlowOfEvents {}

sig AlternativeFlow extends FlowOfEvents {}

abstract sig Step {}

sig Action extends Step {}

sig ControlStatement extends Step {}

//======================================================
// FACTS
//======================================================

//------------------------------------------------------
// Use Case - Textual Description ownership
//------------------------------------------------------

fact UniqueTextualDescriptions {
all uc1, uc2: UseCase |
uc1 != uc2 implies uc1.textualDesc != uc2.textualDesc
}

fact TextualDescriptionOwnership {
all td: TextualDescription |
one uc: UseCase | uc.textualDesc = td
}

//------------------------------------------------------
// Flow ownership
//------------------------------------------------------

fact BasicFlowOwnership {
all bf: BasicFlow |
one td: TextualDescription |
td.basicFlow = bf
}

fact AlternativeFlowOwnership {
all af: AlternativeFlow |
one td: TextualDescription |
af in td.alternativeFlow
}

//------------------------------------------------------
// Step ownership
//------------------------------------------------------

fact StepBelongsToFlow {
all s: Step |
one f: FlowOfEvents |
s in f.steps_
}

//------------------------------------------------------
// Directed relationship constraints
//------------------------------------------------------

fact NoSelfDirectedRelation {
all dr: DirectedRelationship |
dr.source != dr.target
}

fact NoDuplicateDirectedRelationships {


all i1, i2: Include |
    (i1.source = i2.source and
     i1.target = i2.target)
    implies i1 = i2

all e1, e2: Extend |
    (e1.source = e2.source and
     e1.target = e2.target)
    implies e1 = e2

all g1, g2: Generalization |
    (g1.source = g2.source and
     g1.target = g2.target)
    implies g1 = g2


}

//------------------------------------------------------
// Include relationship semantics
//------------------------------------------------------

fact IncludeBelongsToSourceBasicFlow {
all i: Include |
i.ownerFlow = i.source.textualDesc.basicFlow
}

//------------------------------------------------------
// Extend relationship semantics
//------------------------------------------------------

fact ExtendBelongsToTargetAltFlow {
all e: Extend |
e.ownerAltFlow in e.target.textualDesc.alternativeFlow
}

fact ExtensionPointOwnership {
all ep: ExtensionPoint |
one uc: UseCase |
ep in uc.extensionPoints
}

//------------------------------------------------------
// Consistency of textual description elements
//------------------------------------------------------

fact TextualDescriptionElements {

all td: TextualDescription | {

    one td.basicFlow

    some td.triggers
    some td.preconditions
    some td.postconditions
    some td.objectTags
}

}

//======================================================
// EXAMPLE INSTANCE
//======================================================

pred exampleScenario {

some UseCase
some Actor

some TextualDescription

some BasicFlow
some AlternativeFlow

some Step

some Include
some Extend

some ExtensionPoint


}

//======================================================
// RUN
//======================================================

run exampleScenario for 10
