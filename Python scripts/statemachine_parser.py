import xml.etree.ElementTree as ET

XMI_NS = "http://schema.omg.org/spec/XMI/2.1"
XMI = f"{{{XMI_NS}}}"


class AlloyStateMachine:
    def __init__(self, id, name, owner_class_id=None):
        self.id = id
        self.name = name
        self.owner_class_id = owner_class_id
        self.states = []
        self.transitions = []


class AlloyState:
    def __init__(self, id, name, machine):
        self.id = id
        self.name = name
        self.machine = machine
        self.incoming = []
        self.outgoing = []


class AlloyTransition:
    def __init__(self, id, name, machine, source, target):
        self.id = id
        self.name = name              # 🔹 transition name = event
        self.machine = machine
        self.source = source
        self.target = target
        self.guard = None


class AlloyGuard:
    def __init__(self, id, transition, value):
        self.id = id
        self.transition = transition
        self.value = value


def parse_statemachine(xmi_file):

    tree = ET.parse(xmi_file)
    root = tree.getroot()

    # --------------------------------------------------
    # Parent map (to detect owning class)
    # --------------------------------------------------
    parent_map = {child: parent for parent in root.iter() for child in parent}

    state_machines = {}
    states = {}
    transitions = {}
    guards = {}

    # --------------------------------------------------
    # Find ALL StateMachines
    # --------------------------------------------------
    sms = root.findall(".//*[@xmi:type='uml:StateMachine']", {"xmi": XMI_NS})

    for sm in sms:
        sm_id = sm.get(f"{XMI}id")
        sm_name = sm.get("name", "StateMachine")

        # --------------------------------------------------
        # Detect owning class (if any)
        # --------------------------------------------------
        owner_class_id = None
        parent = parent_map.get(sm)

        while parent is not None:
            xmi_type = parent.get(f"{XMI}type") or parent.get("xmi:type")
            if xmi_type == "uml:Class":
                owner_class_id = parent.get(f"{XMI}id")
                break
            parent = parent_map.get(parent)

        sm_obj = AlloyStateMachine(sm_id, sm_name, owner_class_id)
        state_machines[sm_id] = sm_obj

        # --------------------------------------------------
        # Region (single-region assumption, as in your XMI)
        # --------------------------------------------------
        region = sm.find("region")
        if region is None:
            continue

        # --------------------------------------------------
        # States (incl. pseudo & final)
        # --------------------------------------------------
        for sub in region.findall("subvertex"):
            s_id = sub.get(f"{XMI}id")
            s_name = sub.get("name", "State")

            st = AlloyState(s_id, s_name, sm_id)
            states[s_id] = st
            sm_obj.states.append(s_id)

        # --------------------------------------------------
        # Transitions (= events)
        # --------------------------------------------------
        for tr in region.findall("transition"):
            t_id = tr.get(f"{XMI}id")
            t_name = tr.get("name", "")     # 🔹 event name
            src = tr.get("source")
            tgt = tr.get("target")

            t = AlloyTransition(t_id, t_name, sm_id, src, tgt)
            transitions[t_id] = t
            sm_obj.transitions.append(t_id)

            if src in states:
                states[src].outgoing.append(t_id)
            if tgt in states:
                states[tgt].incoming.append(t_id)

            # --------------------------------------------------
            # Guard (optional)
            # --------------------------------------------------
            owned_rule = tr.find("ownedRule")
            if owned_rule is not None:
                g_id = owned_rule.get(f"{XMI}id")
                spec = owned_rule.find("specification")
                value = ""

                if spec is not None:
                    value = (
                        spec.get("value")
                        or spec.get("body")
                        or ""
                    )
                    if not value:
                        body = spec.find("body")
                        if body is not None and body.text:
                            value = body.text.strip()

                g = AlloyGuard(g_id, t_id, value)
                guards[g_id] = g
                t.guard = g_id

    return {
        "stateMachines": state_machines,
        "states": states,
        "transitions": transitions,
        "guards": guards
    }
