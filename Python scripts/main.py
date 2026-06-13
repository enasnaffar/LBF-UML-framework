from usecase_parser import parse_usecase
from classdiagram_parser import parse_classdiagram
from sequence_parser import parse_sequence
from activity_parser import parse_activity
from statemachine_parser import parse_statemachine
from uc_rules import run_uc_rules

import time
def main():
    start_time = time.perf_counter()

    xmi_path = r"C:\Users\Owner\PycharmProjects\UML_Alloy 3\online shopping v33.xmi"

    print("\n==============================")
    print("📌 Parsing XMI File")
    print("==============================")
    print("Input:", xmi_path)

    # ------------------------------------------------------
    # Parse models
    # ------------------------------------------------------
    usecase_data = parse_usecase(xmi_path)
    class_data = parse_classdiagram(xmi_path)
    seq_data = parse_sequence(xmi_path)
    activity_data = parse_activity(xmi_path)
    state_data = parse_statemachine(xmi_path)


    print("\n======================================")
    print("📘 Parsed USE CASE Model")
    print("======================================")
    # ------------------------------------------------------
    # 1. Use case
    # ------------------------------------------------------
    for uc, data in usecase_data.items():
        print(f"\n⭖ Use Case: {uc}")
        print("  UC-ID:", data.get("id"))
        print("  ObjectTags:", data.get("objectTags"))
        print("  trigger:", data.get("trigger"))
        print("  Actors 👤:", data.get("usecaseActors"))
        print("  BasicFlow:", data.get("basicFlowSteps"))
        print("  AlternativeFlow:", data.get("alternativeFlowSteps"))
        print("  Includes:", data.get("includes"))
        print("  Extends:", data.get("extends"))
        print("  Generalizations:", data.get("generalizations"))


    # ------------------------------------------------------
    # 2. CLASS DIAGRAM
    # ------------------------------------------------------
    print("\n======================================")
    print("📘 CLASS DIAGRAM (STRUCTURED)")
    print("======================================\n")

    classes = class_data["classes"]
    properties = class_data["properties"]
    operations = class_data["operations"]
    parameters = class_data["parameters"]
    associations = class_data["associations"]
    generalizations = class_data["generalizations"]

    for cid, c in classes.items():

        cname = c["name"]
        print(f"🟦 Class: {cname}")

        # -----------------------------
        # PROPERTIES
        # -----------------------------
        class_props = [
            p for p in properties.values()
            if p["ownerClass"] == cid
        ]

        if class_props:
            print("  Properties:")
            for p in class_props:
                pname = p["name"]
                lower = p["lower"]
                upper = p["upper"]
                if upper == "*":
                    mult = f"{lower}..*"
                else:
                    mult = f"{lower}..{upper}"
                print(f"    • {pname}  {mult}")
        else:
            print("  Properties: (none)")

        # -----------------------------
        # OPERATIONS
        # -----------------------------
        class_ops = [
            (opid, operations[opid])
            for opid in operations
            if operations[opid]["owner"] == cid
        ]

        if class_ops:
            print("  Operations:")
            for opid, op in class_ops:
                op_name = op["name"]
                print(f"    • {op_name}")

                op_params = [
                    p for p in parameters.values()
                    if p["ownerOp"] == opid
                ]

                for prm in op_params:
                    pname = prm["name"]
                    ptype = prm["type"]
                    lower = prm["lower"]
                    upper = prm["upper"]

                    if upper == "*":
                        mult = f"{lower}..*"
                    else:
                        mult = f"{lower}..{upper}"

                    print(f"        - {pname}:{ptype} {mult}")
        else:
            print("  Operations: (none)")

        print()

    # -----------------------------
    # GENERALIZATIONS
    # -----------------------------
    if generalizations:
        print("Generalizations:")
        for gen in generalizations:
            parent = classes[gen["parent"]]["name"]
            child = classes[gen["child"]]["name"]
            print(f"  {child} → {parent}")
    else:
        print("Generalizations: (none)")

    print()

    # ------------------------------------------------------
    # 3. Sequence Diagram Model
    # ------------------------------------------------------
    print("\n======================================")
    print("📘 Parsed SEQUENCE DIAGRAM Model")
    print("======================================")

    lifelines = seq_data.get("lifelines", {})
    messages = seq_data.get("messages", {})
    uses = seq_data.get("interaction_uses", {})
    names = seq_data.get("interaction_names", {})

    if not lifelines:
        print("⚠ No sequence diagrams found.")
    else:
        for inter_id in lifelines.keys():

            inter_name = names.get(inter_id, "(no name)")

            print(f"\n🟦 Interaction: {inter_name}  (ID={inter_id})")

            print("  Lifelines:")
            for ll_id, cls_name in lifelines[inter_id].items():
                print(f"    - {ll_id}: {cls_name}")

            print("  Messages:")
            for m in messages.get(inter_id, []):
                print(f"    → {m['name']}  (sort={m['sort']})")

            print("  Interaction Uses:")
            for u in uses.get(inter_id, []):

                ref_id = u["refersTo"]
                ref_name = names.get(ref_id, "(unknown interaction)")

                if u["inside_cf"]:
                    op = u.get("cf_operator") or "fragment"
                    print(f"    - refersTo={ref_id} → {ref_name}  (inside {op})")
                else:
                    print(f"    - refersTo={ref_id} → {ref_name}  (top-level)")

    # ------------------------------------------------------
    # 4. Activity Model
    # ------------------------------------------------------
    print("\n======================================")
    print("📘 Parsed ACTIVITY DIAGRAM Model")
    print("======================================\n")

    activities = activity_data["activities"]
    nodes = activity_data["nodes"]
    edges = activity_data["edges"]

    if not activities:
        print("⚠ No activities found.\n")
    else:
        for aid, act in activities.items():
            print(f"🟦 Activity: {act['name']}")

            print("  Nodes:")
            for nid in act["nodes"]:
                n = nodes[nid]
                print(f"    • {n['name']}  (type={n['uml_type']}, role={n['kind']})")

                if n["incoming_ids"]:
                    incoming_names = [
                        nodes[i]["name"] if i in nodes else i
                        for i in n["incoming_ids"]
                    ]
                    print(f"        incoming: {', '.join(incoming_names)}")

                if n["outgoing_ids"]:
                    outgoing_names = [
                        nodes[o]["name"] if o in nodes else o
                        for o in n["outgoing_ids"]
                    ]
                    print(f"        outgoing: {', '.join(outgoing_names)}")

            print("  Edges:")
            for eid in act["edges"]:
                e = edges[eid]
                src_name = nodes[e["source"]]["name"] if e["source"] in nodes else e["source"]
                tgt_name = nodes[e["target"]]["name"] if e["target"] in nodes else e["target"]
                print(f"    • {src_name} → {tgt_name}  [{e['kind']}]")

            print()

    # ------------------------------------------------------
    # 5. State Machine Model
    # ------------------------------------------------------
    print("\n======================================")
    print("📘 Parsed STATE MACHINE Model")
    print("======================================")

    sms = state_data["stateMachines"]
    states = state_data["states"]
    transitions = state_data["transitions"]
    guards = state_data["guards"]

    if not sms:
        print("⚠ No state machines found.\n")
    else:
        for sm_id, sm in sms.items():

            print(f"\n🟥 State Machine: {sm.name}")

            print("  States:")
            if sm.states:
                for sid in sm.states:
                    s = states[sid]
                    print(f"    • {s.name}")
            else:
                print("    (none)")

            print("  Transitions:")
            if sm.transitions:
                for tid in sm.transitions:
                    t = transitions[tid]
                    src_name = states[t.source].name if t.source in states else t.source
                    tgt_name = states[t.target].name if t.target in states else t.target
                    print(f"    • {t.name}: {src_name} → {tgt_name}")
                    if t.guard:
                        g = guards[t.guard]
                        print(f"         guard: {g.value}")
            else:
                print("    (none)")

            print()

    # ------------------------------------------------------
    # 6) RUN RULES
    # ------------------------------------------------------
    report = run_uc_rules(
        usecase_data=usecase_data,
        class_data=class_data,
        seq_data=seq_data,
        ad_data=activity_data,
        sm_data=state_data
    )

    print("\n======================================")
    print("🔍 Consistency Rules Results")
    print("======================================")

    for rule_name, result in report.items():
        print(f"\n=== {rule_name} ===")
        print(result)

    print("\n======================================")
    print("✔ DONE")
    print("======================================\n")
    end_time = time.perf_counter()

    print(f"\nTotal execution time: {end_time - start_time:.4f} seconds")

if __name__ == "__main__":
    main()
