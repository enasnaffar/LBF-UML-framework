import re


def normalize(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip().lower())


# =====================================================================
# 1) INTRA–USE CASE RULES
# =====================================================================

def rule_no_self_directed_relations(usecase_data):
    errors = []

    for uc_name, data in usecase_data.items():

        for inc in data.get("includes", []):
            if inc["baseId"] == inc["fragmentId"]:
                errors.append(f"[Include] Use case '{uc_name}' includes itself.")

        for ext in data.get("extends", []):
            if ext["baseId"] == ext["fragmentId"]:
                errors.append(f"[Extend] Use case '{uc_name}' extends itself.")

        for gen in data.get("generalizations", []):
            if gen["childId"] == gen["parentId"]:
                errors.append(f"[Generalization] '{uc_name}' generalizes itself.")

    return errors


def rule_no_duplicate_directed_relations(usecase_data):
    errors = []
    seen_inc = set()
    seen_ext = set()
    seen_gen = set()

    for uc_name, data in usecase_data.items():

        for inc in data.get("includes", []):
            key = (inc["baseId"], inc["fragmentId"])
            if key in seen_inc:
                errors.append(f"[Include] Duplicate include: {key}")
            seen_inc.add(key)

        for ext in data.get("extends", []):
            key = (ext["baseId"], ext["fragmentId"])
            if key in seen_ext:
                errors.append(f"[Extend] Duplicate extend: {key}")
            seen_ext.add(key)

        for gen in data.get("generalizations", []):
            key = (gen["childId"], gen["parentId"])
            if key in seen_gen:
                errors.append(f"[Generalization] Duplicate generalization: {key}")
            seen_gen.add(key)

    return errors


def rule_each_usecase_has_basic_flow_steps(usecase_data):
    errors = []
    for uc_name, data in usecase_data.items():
        if not data.get("basicFlowSteps"):
            errors.append(f"[BasicFlow] Use case '{uc_name}' has no basic flow steps.")
    return errors


# =====================================================================
# 1) UC–CD RULE
# =====================================================================
# =====================================================================
# 1) UC–CD RULE (UPDATED: CASE-INSENSITIVE + ROBUST)
# =====================================================================


def split_object_tags(tags):
    """
    Handles cases like:
    ["Account, customer"] → ["Account", "customer"]
    """
    out = []
    for t in tags or []:
        parts = re.split(r"[;,]", t)
        out.extend([p.strip() for p in parts if p.strip()])
    return out


def rule_uc_cd_objecttags(usecase_data, class_data):
    errors = []

    # Normalize class names once
    class_names_norm = {
        normalize(c["name"])
        for c in class_data.get("classes", {}).values()
        if c.get("name")
    }

    for uc_name, uc in usecase_data.items():
        tags = split_object_tags(uc.get("objectTags", []))

        for tag in tags:
            if normalize(tag) not in class_names_norm:
                errors.append(
                    f"[ObjectTag] In Use Case '{uc_name}', objectTag '{tag}' "
                    f"is NOT a Class Diagram class ."
                )

    return errors if errors else "No violation detected"


# =====================================================================
# 2) UC–SEQ OBJECT TAG RULE
# =====================================================================
import re
from typing import Any, Dict, List


def rule_uc_seq_objecttags(usecase_data: Dict[str, Dict[str, Any]], seq_data: Dict[str, Any]):
    """
    UC–SEQ ObjectTag rule (name OR type aware):
    For each Use Case, every objectTag must be represented in the corresponding Interaction
    by at least one lifeline. A lifeline can represent an objectTag via:
      - its represented type/class name (e.g., r2:Item -> "Item"), OR
      - its own lifeline name (e.g., name="item"), OR
      - a combined label stored as "r2:Item" (we match both sides).
    """

    def _norm(s: str) -> str:
        return re.sub(r"\s+", " ", s.strip().lower())

    def _add_candidates(represented: set, raw: Any) -> None:
        """
        Add match candidates from a lifeline representation.

        Supported lifeline value formats in seq_data["lifelines"][inter_id].values():
          1) "Item"              -> adds "item"
          2) "r2:Item"           -> adds "r2" and "item" (and the whole string)
          3) {"name": "r2", "type": "Item"} -> adds "r2" and "item"
          4) {"lifeline_name": "...", "represented_type": "..."} -> adds both
        """
        if raw is None:
            return

        # Dict-based (recommended if you store name and type separately)
        if isinstance(raw, dict):
            name = raw.get("name") or raw.get("lifeline_name")
            typ = raw.get("type") or raw.get("represented_type") or raw.get("class") or raw.get("classifier")
            label = raw.get("label")

            if isinstance(label, str) and label.strip():
                represented.add(_norm(label))

                # If label includes "x:y", add both parts too
                if ":" in label:
                    left, right = label.split(":", 1)
                    if left.strip():
                        represented.add(_norm(left))
                    if right.strip():
                        represented.add(_norm(right))

            if isinstance(name, str) and name.strip():
                represented.add(_norm(name))

            if isinstance(typ, str) and typ.strip():
                represented.add(_norm(typ))

            return

        # String-based (backward-compatible)
        if isinstance(raw, str):
            s = raw.strip()
            if not s:
                return

            represented.add(_norm(s))

            # If stored like "r2:Item", add both sides as candidates
            if ":" in s:
                left, right = s.split(":", 1)
                if left.strip():
                    represented.add(_norm(left))
                if right.strip():
                    represented.add(_norm(right))

            return

        # Unknown format: ignore
        return

    errors: List[str] = []

    uc_to_inter = seq_data.get("uc_to_interaction", {})
    lifelines = seq_data.get("lifelines", {})

    for uc_name, uc in usecase_data.items():
        uc_id = uc.get("id")

        tags = [
            _norm(t) for t in uc.get("objectTags", [])
            if isinstance(t, str) and t.strip()
        ]

        # No tags -> nothing to validate for this rule
        if not tags:
            continue

        # If no mapping to an interaction, skip (other rules may handle this)
        if uc_id not in uc_to_inter:
            continue

        inter_id = uc_to_inter[uc_id]
        inter_lifelines = lifelines.get(inter_id)

        # Interaction has no lifelines at all -> violation for each required tag
        if not inter_lifelines:
            for t in tags:
                errors.append(
                    f"[UC-SEQ ObjectTag] Use Case '{uc_name}' requires objectTag '{t}', "
                    f"but Interaction '{inter_id}' has no lifelines."
                )
            continue

        # Build candidate set from both lifeline names and represented types
        represented = set()
        for v in inter_lifelines.values():
            _add_candidates(represented, v)

        # Check each objectTag exists in candidate set
        for t in tags:
            if t not in represented:
                errors.append(
                    f"[UC-SEQ ObjectTag] Use Case '{uc_name}' requires objectTag '{t}', "
                    f"but Interaction '{inter_id}' does not represent it "
                    f"(checked lifeline names and represented types)."
                )

    return errors if errors else "No violation detected"


# =====================================================================
# 3) UC–SEQ TRIGGER RULE
# =====================================================================

def rule_uc_seq_trigger(usecase_data, seq_data):
    errors = []

    uc_to_inter = seq_data.get("uc_to_interaction", {})
    messages = seq_data.get("messages", {})
    interaction_names = seq_data.get("interaction_names", {})

    for uc_name, uc in usecase_data.items():

        trigger = uc.get("trigger")
        uc_id = uc.get("id")

        if uc_id not in uc_to_inter:
            continue

        inter_id = uc_to_inter[uc_id]
        inter_msgs = messages.get(inter_id, [])

        if not inter_msgs:
            continue

        first_msg = None

        for m in inter_msgs:
            if m["sort"] == "reply":
                continue

            if not m["name"]:
                inter_label = interaction_names.get(inter_id, inter_id)
                errors.append(
                    f"[UC-SEQ Trigger] Interaction '{inter_label}' "
                    f"contains an unnamed non-reply message."
                )
                break

            first_msg = m
            break

        if not first_msg:
            continue

        if trigger:
            if trigger.lower().strip() not in first_msg["name"].lower():
                inter_label = interaction_names.get(inter_id, inter_id)
                errors.append(
                    f"[UC-SEQ Trigger] Use Case '{uc_name}' has trigger '{trigger}', "
                    f"but first message is '{first_msg['name']}' "
                    f"in Interaction '{inter_label}'."
                )

    return errors if errors else "No violation detected"


# =====================================================================
# 4) Alternative Flow → Decision Node in Activity Diagram
# =====================================================================

def rule_uc_ad_alternative_flow_decision(usecase_data, ad_data):
    """
    Rule:
    If a use case has at least one alternative flow step AND
    it has a corresponding Activity Diagram,
    then that Activity Diagram must contain at least one DecisionNode.
    """

    errors = []
    any_applicable = False

    decision_nodes_by_activity = {}

    for node_id, node in ad_data.get("nodes", {}).items():
        if node.get("kind") == "DecisionNode":
            act = node.get("activity")
            if act:
                decision_nodes_by_activity.setdefault(act, []).append(node_id)

    for uc_name, uc in usecase_data.items():

        alt_steps = uc.get("alternativeFlowSteps", [])
        if not alt_steps:
            continue

        activity_id = uc.get("activity_id")

        if not activity_id:
            continue

        any_applicable = True

        has_decision = len(decision_nodes_by_activity.get(activity_id, [])) > 0

        if not has_decision:
            errors.append(
                f"[AlternativeFlowDecision] Use Case '{uc_name}' has alternative flows, "
                f"but its Activity Diagram '{activity_id}' contains NO DecisionNode."
            )

    if not any_applicable:
        return "Rule does not Apply"

    return errors if errors else "No violation detected"


# =====================================================================
# 5) INCLUDE RULE
# =====================================================================

def rule_uc_seq_include_ref(usecase_data, seq_data):
    errors = []
    applicable = False

    uc_to_inter = seq_data["uc_to_interaction"]
    inter_uses = seq_data["interaction_uses"]

    for uc in usecase_data.values():
        for inc in uc.get("includes", []):
            parent_id = inc["baseId"]
            child_id = inc["fragmentId"]

            parent_has_seq = parent_id in uc_to_inter
            child_has_seq = child_id in uc_to_inter

            if parent_has_seq != child_has_seq:
                continue

            if not parent_has_seq:
                continue

            applicable = True

            s1 = uc_to_inter[parent_id]
            s2 = uc_to_inter[child_id]

            uses = inter_uses.get(s1, [])

            if not any(u["refersTo"] == s2 for u in uses):
                errors.append(
                    f"[UC-SEQ Include] '{inc['baseName']}' includes '{inc['fragmentName']}', "
                    f"but Interaction '{s1}' does NOT reference '{s2}'."
                )

    return applicable, errors


# =====================================================================
# 6) EXTEND RULE
# =====================================================================

def rule_uc_seq_extend_ref(usecase_data, seq_data):
    errors = []
    applicable = False

    uc_to_inter = seq_data["uc_to_interaction"]
    inter_uses = seq_data["interaction_uses"]

    for uc in usecase_data.values():
        for ext in uc.get("extends", []):
            parent_id = ext["baseId"]
            child_id = ext["fragmentId"]

            parent_has_seq = parent_id in uc_to_inter
            child_has_seq = child_id in uc_to_inter

            if parent_has_seq != child_has_seq:
                continue

            if not parent_has_seq:
                continue

            applicable = True

            s1 = uc_to_inter[parent_id]
            s2 = uc_to_inter[child_id]

            uses = inter_uses.get(s1, [])

            if not any(u["refersTo"] == s2 for u in uses):
                errors.append(
                    f"[UC-SEQ Extend] '{ext['baseName']}' is extended by '{ext['fragmentName']}', "
                    f"but Interaction '{s1}' does NOT reference '{s2}'."
                )
                continue

            if not any(
                    u["refersTo"] == s2 and u.get("inside_cf") for u in uses
            ):
                errors.append(
                    f"[UC-SEQ Extend] Interaction '{s1}' references '{s2}', "
                    f"but NOT inside opt/alt/break."
                )

    return applicable, errors


# =====================================================================
# 7) SM–UC trigger RULE
# =====================================================================

def normalize(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip().lower())


def split_object_tags(tags):
    """
    Handles cases like: ["Account, customer"] -> ["Account", "customer"]
    """
    out = []
    for t in tags or []:
        if not t:
            continue
        parts = re.split(r"[;,]", t)  # split on comma/semicolon
        out.extend([p.strip() for p in parts if p.strip()])
    return out


def get_sm_owner_id(sm):
    """
    Supports both object-style and dict-style state machine records.
    Tries multiple likely field names used by parsers.
    """
    # object style
    for attr in ("owner_class_id", "ownerClassId", "owner_id", "ownerId", "ownerClass", "owner"):
        if hasattr(sm, attr):
            val = getattr(sm, attr)
            if val:
                return val

    # dict style
    if isinstance(sm, dict):
        for k in ("owner_class_id", "ownerClassId", "owner_id", "ownerId", "ownerClass", "owner"):
            val = sm.get(k)
            if val:
                return val

    return None
def rule_uc_sm_trigger(usecase_data, class_data, sm_data):
    """
    Rule:
    If a Use Case has a trigger AND
    at least one tagged object belongs to a Class that owns a StateMachine,
    THEN the trigger must match a state-changing transition name
    in at least one of those StateMachines.

    Applicability:
    - No trigger -> rule does not apply
    - No tagged object with an owned StateMachine -> rule does not apply
    """

    errors = []
    applicable = False

    classes = class_data.get("classes", {})

    # class name -> class id
    class_name_to_id = {
        normalize(c.get("name")): cid
        for cid, c in classes.items()
        if c.get("name")
    }

    state_machines = sm_data.get("stateMachines", {})
    transitions = sm_data.get("transitions", {})

    explain_not_applicable = []

    for uc_name, uc in usecase_data.items():

        trigger = uc.get("trigger")
        if not trigger:
            continue

        trigger_norm = normalize(trigger)

        raw_tags = uc.get("objectTags", [])
        tags = split_object_tags(raw_tags)

        if not tags:
            explain_not_applicable.append(
                f"[UC-SM Trigger] '{uc_name}': has trigger '{trigger}', but objectTags list is empty."
            )
            continue

        any_class_found = False
        any_owned_sm_found = False
        trigger_found_in_any_sm = False

        for tag in tags:

            c_id = class_name_to_id.get(normalize(tag))

            if not c_id:
                continue

            any_class_found = True

            owned_sms = []

            for sm in state_machines.values():
                owner_id = get_sm_owner_id(sm)

                if owner_id == c_id:
                    owned_sms.append(sm)

            if not owned_sms:
                continue

            any_owned_sm_found = True
            applicable = True

            for sm in owned_sms:

                sm_transitions = getattr(sm, "transitions", None)

                if sm_transitions is None and isinstance(sm, dict):
                    sm_transitions = sm.get("transitions", [])

                for t_id in sm_transitions or []:

                    t = transitions.get(t_id)

                    if not t:
                        continue

                    t_name = getattr(t, "name", None)

                    if t_name is None and isinstance(t, dict):
                        t_name = t.get("name")

                    if not t_name:
                        continue

                    t_source = getattr(t, "source", None)

                    if t_source is None and isinstance(t, dict):
                        t_source = t.get("source")

                    t_target = getattr(t, "target", None)

                    if t_target is None and isinstance(t, dict):
                        t_target = t.get("target")

                    # only state-changing transitions count
                    if t_source == t_target:
                        continue

                    if normalize(t_name) == trigger_norm:
                        trigger_found_in_any_sm = True
                        break

                if trigger_found_in_any_sm:
                    break

            if trigger_found_in_any_sm:
                break

        if any_owned_sm_found and not trigger_found_in_any_sm:
            errors.append(
                f"[UC-SM Trigger] Use Case '{uc_name}' has trigger '{trigger}', "
                f"but no matching state-changing transition was found in any "
                f"StateMachine associated with its tagged objects."
            )

        if not any_class_found:
            explain_not_applicable.append(
                f"[UC-SM Trigger] '{uc_name}': trigger exists ('{trigger}') but none "
                f"of objectTags {tags} matched any Class name."
            )

        elif not any_owned_sm_found:
            explain_not_applicable.append(
                f"[UC-SM Trigger] '{uc_name}': trigger exists ('{trigger}') and "
                f"objectTags matched Classes, but no owned StateMachine was found."
            )

    if not applicable:
        if explain_not_applicable:
            return ["Rule does not apply (details):"] + explain_not_applicable
        else:
            return "Rule does not apply"

    return errors if errors else "No violation detected"

# =====================================================================
# 8) MAIN RULE RUNNER
# =====================================================================
def run_uc_rules(usecase_data, class_data=None, seq_data=None, ad_data=None, sm_data=None):
    report = {}

    report["NoSelfDirectedRelations"] = rule_no_self_directed_relations(usecase_data)
    report["NoDuplicateDirectedRelations"] = rule_no_duplicate_directed_relations(usecase_data)
    report["EachUseCaseHasBasicFlowSteps"] = rule_each_usecase_has_basic_flow_steps(usecase_data)

    if class_data:
        report["📊 RULE 1 : UC_CD_ObjectTags"] = rule_uc_cd_objecttags(usecase_data, class_data)

    if seq_data:
        report["📊 RULE 2 : UC_SEQ_ObjectTags"] = rule_uc_seq_objecttags(usecase_data, seq_data)
        report["📊 RULE 3 : UC_SEQ_Trigger"] = rule_uc_seq_trigger(usecase_data, seq_data)

    if ad_data:
        report["📊 RULE 4 : UC_AD_AlternativeFlowDecision"] = (
            rule_uc_ad_alternative_flow_decision(usecase_data, ad_data)
        )
    if seq_data:
        applicable, errors = rule_uc_seq_include_ref(usecase_data, seq_data)
        report["📊 RULE 5 : UC_SEQ_IncludeRef"] = (
            "Rule does not apply." if not applicable else
            "No violations detected." if not errors else errors
        )

        applicable, errors = rule_uc_seq_extend_ref(usecase_data, seq_data)
        report["📊 RULE 6 : UC_SEQ_ExtendRef"] = (
            "Rule does not apply." if not applicable else
            "No violations detected." if not errors else errors
        )

    if sm_data and class_data:
        # ✅ 🔥 THIS WAS MISSING
        report["📊 RULE 7 : UC_SM_Trigger"] = (
            rule_uc_sm_trigger(usecase_data, class_data, sm_data)
        )

    return report
