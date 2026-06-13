import xml.etree.ElementTree as ET

NS_XMI = "http://schema.omg.org/spec/XMI/2.1"
NS = {"xmi": NS_XMI}

def get_id(elem):
    return elem.attrib.get(f"{{{NS_XMI}}}id") or elem.attrib.get("xmi:id")

def get_type(elem):
    return elem.attrib.get(f"{{{NS_XMI}}}type") or elem.attrib.get("xmi:type")


def parse_sequence(xmi_path):
    tree = ET.parse(xmi_path)
    root = tree.getroot()

    seq_data = {
        "uc_to_interaction": {},
        "lifelines": {},          # inter_id -> { lifeline_id: {"name":..., "type":...} }
        "lifeline_types": {},     # inter_id -> { lifeline_id: type_name_or_None }
        "messages": {},
        "interaction_uses": {},
        "interaction_names": {}
    }

    # ============================================================
    # 1) USE CASE → OWNED INTERACTION
    # ============================================================
    for uc in root.iter():
        if get_type(uc) != "uml:UseCase":
            continue

        uc_id = get_id(uc)
        for beh in uc.findall("{*}ownedBehavior"):
            if get_type(beh) == "uml:Interaction":
                seq_data["uc_to_interaction"][uc_id] = get_id(beh)

    # ============================================================
    # 2) COLLECT ALL INTERACTIONS
    # ============================================================
    interactions = [inter for inter in root.iter() if get_type(inter) == "uml:Interaction"]

    # ============================================================
    # 3) PARSE EACH INTERACTION
    # ============================================================
    for inter in interactions:
        inter_id = get_id(inter)
        inter_name = inter.attrib.get("name", "")

        seq_data["interaction_names"][inter_id] = inter_name
        seq_data["lifelines"][inter_id] = {}
        seq_data["lifeline_types"][inter_id] = {}
        seq_data["messages"][inter_id] = []
        seq_data["interaction_uses"][inter_id] = []

        # --------------------------------------------------------
        # Lifelines: build map from ownedAttribute id -> type name
        # (lifeline@represents points to ownedAttribute xmi:id)
        # --------------------------------------------------------
        attr_type_map = {}

        collab = inter.find("{*}nestedClassifier")
        if collab is not None:
            for attr in collab.findall("{*}ownedAttribute"):
                attr_id = get_id(attr)
                type_id = attr.attrib.get("type")  # points to classifier xmi:id
                if attr_id and type_id:
                    cls = root.find(f".//*[@xmi:id='{type_id}']", NS)
                    if cls is not None:
                        attr_type_map[attr_id] = cls.attrib.get("name")

        # Lifelines: store BOTH name and type
        for ll in inter.findall("{*}lifeline"):
            ll_id = get_id(ll)
            ll_name = (ll.attrib.get("name") or "").strip()  # <lifeline name="item"/>
            prop_id = ll.attrib.get("represents")            # points to ownedAttribute id
            type_name = attr_type_map.get(prop_id)           # resolved classifier name, or None

            # Store dict for the updated rule (name OR type matching)
            seq_data["lifelines"][inter_id][ll_id] = {
                "name": ll_name if ll_name else None,
                "type": type_name if type_name else None
            }

            # Keep old structure if you need it elsewhere
            seq_data["lifeline_types"][inter_id][ll_id] = type_name if type_name else None

        # --------------------------------------------------------
        # Messages (ORDERED by fragments)
        # --------------------------------------------------------
        msg_map = {}

        for msg in inter.findall("{*}message"):
            msg_id = get_id(msg)
            if not msg_id:
                continue

            msg_map[msg_id] = {
                "id": msg_id,
                "name": (msg.attrib.get("name") or "").strip(),
                "sort": msg.attrib.get("messageSort", "call").lower()
            }

        for frag in inter.findall("{*}fragment"):
            if get_type(frag) != "uml:MessageOccurrenceSpecification":
                continue

            mid = frag.attrib.get("message")
            if mid and mid in msg_map:
                seq_data["messages"][inter_id].append(msg_map[mid])

        # --------------------------------------------------------
        # Interaction Uses (top-level + combined fragments)
        # --------------------------------------------------------
        for frag in inter.findall("{*}fragment"):
            if get_type(frag) == "uml:InteractionUse":
                seq_data["interaction_uses"][inter_id].append({
                    "refersTo": frag.attrib.get("refersTo"),
                    "inside_cf": False,
                    "cf_operator": None
                })

            if get_type(frag) == "uml:CombinedFragment":
                op = (frag.attrib.get("interactionOperator", "") or "").lower()
                for operand in frag.findall("{*}operand"):
                    for sub in operand.findall("{*}fragment"):
                        if get_type(sub) == "uml:InteractionUse":
                            seq_data["interaction_uses"][inter_id].append({
                                "refersTo": sub.attrib.get("refersTo"),
                                "inside_cf": True,
                                "cf_operator": op
                            })

    return seq_data
