import xml.etree.ElementTree as ET

NS_XMI = "http://schema.omg.org/spec/XMI/2.1"
NS = {"xmi": NS_XMI}

def get_id(elem):
    return elem.attrib.get(f"{{{NS_XMI}}}id") or elem.attrib.get("xmi:id")

def get_type(elem):
    return elem.attrib.get(f"{{{NS_XMI}}}type") or elem.attrib.get("xmi:type")

def resolve_name(root, elem_id):
    if not elem_id:
        return None
    found = root.find(f".//*[@xmi:id='{elem_id}']", NS)
    return found.attrib.get("name") if found is not None else None


def parse_usecase(xmi_path):
    try:
        tree = ET.parse(xmi_path)
        root = tree.getroot()
    except Exception as e:
        print("❌ ERROR reading XMI:", e)
        return None

    usecases = {}

    # =====================================================================
    # 1) FIND USE CASES
    # =====================================================================
    for uc in root.iter():
        if get_type(uc) != "uml:UseCase":
            continue

        uc_name = uc.attrib.get("name")
        uc_id = get_id(uc)
        if not uc_name:
            continue

        usecases[uc_name] = {
            "id": uc_id,
            "trigger": None,
            "objectTags": [],
            "basicFlowSteps": [],
            "alternativeFlowSteps": [],
            "includes": [],
            "extends": [],
            "generalizations": [],
            "usecaseActors": [],
            "activity_id": None     # <-- NEW
        }

        # =====================================================================
        # 2) COMMENTS → extract Trigger, Basic Flow, ALT Flow
        # =====================================================================
        for com in uc.findall("ownedComment"):
            body_elem = com.find("body")
            if body_elem is None:
                continue

            text = body_elem.text or ""
            lines = [l.strip() for l in text.split("\n") if l.strip()]

            for line in lines:
                low = line.lower()

                # --- TRIGGER ---
                if low.startswith("trigger:"):
                    usecases[uc_name]["trigger"] = line.split(":", 1)[1].strip()
                    continue

                # --- OBJECT TAG ---
                if low.startswith("objecttag"):
                    tag = line.split(":", 1)[1].strip()
                    usecases[uc_name]["objectTags"].append(tag)
                    continue

                # --- BASIC FLOW ---
                if low.startswith("main flow") or low.startswith("basic flow") or low.startswith("flow of events"):
                    steps = line.split(":", 1)[1]
                    steps = [s.strip() for s in steps.split(",") if s.strip()]
                    usecases[uc_name]["basicFlowSteps"].extend(steps)
                    continue

                # --- ALTERNATIVE FLOW ---
                if (
                    low.startswith("alternative flow") or
                    low.startswith("alternative:") or
                    low.startswith("alternative scenario") or
                    low.startswith("alt flow")
                ):
                    steps = line.split(":", 1)[1]
                    steps = [s.strip() for s in steps.split(",") if s.strip()]
                    usecases[uc_name]["alternativeFlowSteps"].extend(steps)
                    continue

        # =====================================================================
        # 3) INCLUDE
        # =====================================================================
        for inc in uc.findall("include"):
            added_id = inc.attrib.get("addition")
            added_name = resolve_name(root, added_id)

            usecases[uc_name]["includes"].append({
                "baseId": uc_id,
                "baseName": uc_name,
                "fragmentId": added_id,
                "fragmentName": added_name
            })

        # =====================================================================
        # 4) EXTEND
        # =====================================================================
        for ext in uc.findall("extend"):
            parent_id = ext.attrib.get("extendedCase")
            parent_name = resolve_name(root, parent_id)

            usecases[uc_name]["extends"].append({
                "baseId": parent_id,
                "baseName": parent_name,
                "fragmentId": uc_id,
                "fragmentName": uc_name
            })

        # =====================================================================
        # 5) GENERALIZATION
        # =====================================================================
        for gen in uc.findall("generalization"):
            parent_id = gen.attrib.get("general")
            parent_name = resolve_name(root, parent_id)

            usecases[uc_name]["generalizations"].append({
                "childId": uc_id,
                "childName": uc_name,
                "parentId": parent_id,
                "parentName": parent_name
            })

        # =====================================================================
        # 6) FIND ACTORS
        # =====================================================================
    uc_id_map = {v["id"]: k for k, v in usecases.items()}

    for assoc in root.iter():
        if get_type(assoc) != "uml:Association":
            continue

        ends = assoc.findall("ownedEnd")
        if len(ends) != 2:
            continue

        e1, e2 = ends
        t1 = e1.attrib.get("type")
        t2 = e2.attrib.get("type")

        if t1 in uc_id_map and t2 not in uc_id_map:
            actor_name = resolve_name(root, t2)
            usecases[uc_id_map[t1]]["usecaseActors"].append({"id": t2, "name": actor_name})

        if t2 in uc_id_map and t1 not in uc_id_map:
            actor_name = resolve_name(root, t1)
            usecases[uc_id_map[t2]]["usecaseActors"].append({"id": t1, "name": actor_name})

    # =====================================================================
    # 7) **NEW — LINK ACTIVITY DIAGRAMS TO USE CASES**
    # =====================================================================
    for uc in root.iter():
        if get_type(uc) != "uml:UseCase":
            continue

        uc_name = uc.attrib.get("name")
        if uc_name not in usecases:
            continue

        for beh in uc.findall("{*}ownedBehavior"):
            btype = get_type(beh)
            if btype == "uml:Activity":
                usecases[uc_name]["activity_id"] = get_id(beh)

    return usecases
