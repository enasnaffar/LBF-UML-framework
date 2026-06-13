import xml.etree.ElementTree as ET
import re
import os

def parse_classdiagram(xmi_file):

    uml_ns = "http://www.eclipse.org/uml2/3.0.0/UML"
    xmi_ns = "http://schema.omg.org/spec/XMI/2.1"

    output_dir = r"F:\User Folders\Documents\AlloyModels"
    os.makedirs(output_dir, exist_ok=True)

    alloy_out_name = "CD_uml.als"
    out_path = os.path.join(output_dir, alloy_out_name)

    # -------------------------
    # HELPERS
    # -------------------------
    def sanitize(name: str) -> str:
        if not name:
            name = "Anon"
        name = re.sub(r"\W+", "_", name)
        if not re.match(r"[A-Za-z_]", name[0]):
            name = "X_" + name
        return name

    def get_xmi_type(elem):
        return elem.attrib.get(f"{{{xmi_ns}}}type") or elem.attrib.get("xmi:type") or ""

    def get_xmi_id(elem):
        return elem.attrib.get(f"{{{xmi_ns}}}id") or elem.attrib.get("xmi:id")

    def extract_multiplicity(elem):
        lower = 1
        upper = 1

        lv = elem.find("{*}lowerValue")
        if lv is not None:
            val = lv.attrib.get("value")
            lower = 0 if not val else int(val)

        uv = elem.find("{*}upperValue")
        if uv is not None:
            val = uv.attrib.get("value")
            if val in (None, ""):
                upper = 1
            elif val in ("*", "-1"):
                upper = "*"
            else:
                upper = int(val)

        return lower, upper

    def parse_inline_parameters(op_name):
        m = re.match(r"([A-Za-z0-9_]+)\((.*?)\)(?::(.*))?$", op_name)
        if not m:
            return op_name, [], None
        base_name = m.group(1)
        params_str = m.group(2).strip()
        return_type = m.group(3).strip() if m.group(3) else None
        params = []
        if params_str:
            for p in params_str.split(","):
                p = p.strip()
                if ":" in p:
                    pname, ptype = p.split(":", 1)
                else:
                    pname = p
                    ptype = None
                params.append((pname.strip(), ptype.strip() if ptype else None))
        return base_name, params, return_type

    # ======================================================
    # LOAD XMI
    # ======================================================
    try:
        with open(xmi_file, "r", encoding="utf-8-sig") as f:
            tree = ET.parse(f)
    except Exception as e:
        print("❌ ERROR:", e)
        return None

    root = tree.getroot()

    # ======================================================
    # DATA STRUCTURES
    # ======================================================
    classes = {}
    properties = {}
    operations = {}
    parameters = {}
    associations = {}
    generals = []
    association_owned_property_ids = set()

    # ======================================================
    # 1) COLLECT CLASSES / PROPERTIES / OPERATIONS
    # ======================================================
    for pe in root.findall(".//*"):
        if get_xmi_type(pe) != "uml:Class":
            continue

        cid = get_xmi_id(pe)
        cname = pe.attrib.get("name", f"Class_{cid}")
        classes[cid] = {"name": cname}

        for oa in pe.findall("{*}ownedAttribute"):
            pid = get_xmi_id(oa)
            pname = oa.attrib.get("name", f"attr_{pid}")
            agg = oa.attrib.get("aggregation")
            type_id = oa.attrib.get("type")
            lower, upper = extract_multiplicity(oa)

            properties[pid] = {
                "name": pname,
                "ownerClass": cid,
                "ownerAssociation": None,
                "aggregation": agg,
                "type": type_id,
                "lower": lower,
                "upper": upper,
            }

        for op in pe.findall("{*}ownedOperation"):
            opid = get_xmi_id(op)
            raw_name = op.attrib.get("name", f"op_{opid}")
            operations[opid] = {"name": raw_name, "owner": cid}

            found_real_params = False
            for param in op.findall("{*}ownedParameter"):
                found_real_params = True
                pid = get_xmi_id(param)
                pname = param.attrib.get("name", f"param_{pid}")
                ptype = param.attrib.get("type")
                direction = param.attrib.get("direction", "in")
                lower, upper = extract_multiplicity(param)

                parameters[pid] = {
                    "name": pname,
                    "ownerOp": opid,
                    "type": ptype,
                    "direction": direction,
                    "lower": lower,
                    "upper": upper,
                }

            if not found_real_params:
                base_name, params_inline, return_type = parse_inline_parameters(raw_name)
                operations[opid]["name"] = base_name

                for pname, ptype in params_inline:
                    pid = f"{opid}_{pname}"
                    parameters[pid] = {
                        "name": pname,
                        "ownerOp": opid,
                        "type": ptype,
                        "direction": "in",
                        "lower": 1,
                        "upper": 1,
                    }

                if return_type:
                    pid = f"{opid}_return"
                    parameters[pid] = {
                        "name": "return",
                        "ownerOp": opid,
                        "type": return_type,
                        "direction": "return",
                        "lower": 1,
                        "upper": 1,
                    }

        for gen in pe.findall("{*}generalization"):
            parent_id = gen.attrib.get("general")
            if parent_id in classes:
                generals.append({"parent": parent_id, "child": cid})

    # ======================================================
    # 2) ASSOCIATIONS
    # ======================================================
    for pe in root.findall(".//*"):
        if get_xmi_type(pe) != "uml:Association":
            continue

        aid = get_xmi_id(pe)
        aname = pe.attrib.get("name", f"Assoc_{aid}")
        member_ends = [m for m in pe.attrib.get("memberEnd", "").split() if m]

        owned_ends = []
        for oe in pe.findall("{*}ownedEnd"):
            pid = get_xmi_id(oe)
            owned_ends.append(pid)
            association_owned_property_ids.add(pid)

            pname = oe.attrib.get("name") or f"end_{pid}"
            type_id = oe.attrib.get("type")
            agg = oe.attrib.get("aggregation")
            lower, upper = extract_multiplicity(oe)

            properties[pid] = {
                "name": pname,
                "ownerClass": None,
                "ownerAssociation": aid,
                "aggregation": agg,
                "type": type_id,
                "lower": lower,
                "upper": upper,
            }

        associations[aid] = {
            "name": aname,
            "memberEnd": member_ends,
            "ownedEnds": owned_ends,
        }

    # ======================================================
    # RETURN STRUCTURED DATA (no printing)
    # ======================================================

    return {
        "classes": classes,
        "properties": properties,
        "operations": operations,
        "parameters": parameters,
        "associations": associations,
        "generalizations": generals,
    }
