module CD_new

// --------------------------------------------------
// Core UML Class Concepts
// --------------------------------------------------

sig Class_ {
    ownedAttributes: set Property,          // UML: Class::ownedAttribute
    operations: set Operation
}

// --------------------------------------------------
// Relationships
// --------------------------------------------------

abstract sig Relationship {
    classes: some Class_                    // UML: relationships link ≥1 classes
}
one sig UndefinedClass extends Class_ {}

// UML-style Association hierarchy
abstract sig Association extends Relationship {
    memberEnd: set Property,                // UML: Association::memberEnd
    ownedEnd: set Property                  // UML: Association::ownedEnd
} {
    ownedEnd in memberEnd                   // ownedEnd ⊆ memberEnd
}

sig UnaryAssociation extends Association {}
sig BinaryAssociation extends Association {}
sig NAryAssociation extends Association {}

// Specializations of binary association
sig Composition extends BinaryAssociation {}
sig Aggregation extends BinaryAssociation {}

// --------------------------------------------------
// Generalization
// --------------------------------------------------

sig Generalization extends Relationship {
    parent: one Class_,
    child: one Class_
}

// --------------------------------------------------
// Class Members
// --------------------------------------------------

abstract sig Property extends MultiplicityElement {
    ownerClass: lone Class_,                // owned by Class (attribute or navigable end)
    ownerAssociation: lone Association       // owned by Association (non-navigable end)
} {

    // A Property cannot be owned by both Class and Association
    not (some ownerClass and some ownerAssociation)

    // A Property must have exactly one owner
    one (ownerClass + ownerAssociation)
}

sig Operation {
    parameters: set Parameter
}

sig Parameter extends MultiplicityElement {}

// --------------------------------------------------
// Multiplicity
// --------------------------------------------------

abstract sig MultiplicityElement {
    lower: one Int,
    upper: one Int          // -1 represents UML "*"
}

// --------------------------------------------------
// Facts — UML Semantic Consistency
// --------------------------------------------------

// A relationship must involve at least one class
fact RelationshipHasClasses {
    all r: Relationship | some r.classes
}

// --------------------------------------------------
// Association arity
// --------------------------------------------------

fact AssociationEndCardinality {
    all a: UnaryAssociation  | #a.memberEnd = 2
    all a: BinaryAssociation | #a.memberEnd = 2
    all a: NAryAssociation   | #a.memberEnd = #a.classes
}

// Ends must belong to one of the association's participating classes
fact EndsBelongToClasses {
    all a: Association |
        all p: a.memberEnd | p.ownerClass in a.classes
}

// ownedEnd must correctly reference its owning Association
fact OwnedEndConsistency {
    all a: Association |
        all p: a.ownedEnd | p.ownerAssociation = a
}

// Class-owned attributes must correctly reference their owning Class
fact ClassOwnedAttributesConsistency {
    all c: Class_ |
        all p: c.ownedAttributes | p.ownerClass = c
}

// --------------------------------------------------
// Generalization Constraints
// --------------------------------------------------

fact GeneralizationParentChild {
    all g: Generalization | {
        g.parent != g.child
        g.parent in g.classes
        g.child in g.classes
        #g.classes = 2
    }
}

// --------------------------------------------------
// Association class counts
// --------------------------------------------------

fact AssociationClassCardinality {
    all a: BinaryAssociation | #a.classes = 2
    all a: UnaryAssociation  | #a.classes = 1
}

// Binary associations must connect two distinct classes
fact BinaryAssociationTwoDistinctClasses {
    all b: BinaryAssociation |
        some c1, c2: b.classes | c1 != c2
}

// Unary association ends must belong to the single class
fact UnaryAssociationEndsSameClass {
    all u: UnaryAssociation |
        all p: u.memberEnd | p.ownerClass in u.classes
}

run {} for 4 
