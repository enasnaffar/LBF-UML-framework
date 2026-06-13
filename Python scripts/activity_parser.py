import xml.etree.ElementTree as ET
import re
import os

def parse_activity(xmi_file):
    # ------------------------------------------------------
    # CONFIG
    # ------------------------------------------------------
    XMI_NS = "http://schema.omg.org/spec/XMI/2.1"

    # ------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------
    def get_xmi_type(elem):
        return (
            elem.attrib.get(f"{{{XMI_NS}}}type")
            or elem.attrib.get("xmi:type")
            or ""
        )

    def get_xmi_id(elem):
        return (
            elem.attrib.get(f"{{{XMI_NS}}}id")
            or elem.attrib.get("xmi:id")
        )

    # ------------------------------------------------------
    # LOAD XMI
    # ------------------------------------------------------
    try:
        tree = ET.parse(xmi_file)
        root = tree.getroot()
    except Exception as e:
        print("❌ ERROR reading XMI:", e)
        return None

    # ------------------------------------------------------
    # DATA STRUCTURES
    # ------------------------------------------------------
    activities = {}
    nodes = {}
    edges = {}

    # ⭐ FIXED: MergeNode ADDED ⭐
    NODE_KIND_MAP = {
        "uml:InitialNode": "InitialNode",
        "uml:ActivityFinalNode": "FinalNode",
        "uml:DecisionNode": "DecisionNode",
        "uml:MergeNode": "MergeNode",            # ← FIXED
        "uml:OpaqueAction": "ActivityNode",
    }

    EDGE_KIND_MAP = {
        "uml:ControlFlow": "ControlFlow",
        "uml:ObjectFlow": "ObjectFlow",
    }

    # ------------------------------------------------------
    # 1) FIND ALL ACTIVITIES
    # ------------------------------------------------------
    for act in root.iter():
        if get_xmi_type(act) != "uml:Activity":
            continue

        aid = get_xmi_id(act)
        aname = act.attrib.get("name", f"Activity_{aid}")

        activities[aid] = {"name": aname, "nodes": set(), "edges": set()}

        # ------------------------------------------------------
        # 2) PARSE NODES
        # ------------------------------------------------------
        for ne in act.findall("{*}node"):
            nid = get_xmi_id(ne)
            uml_type = get_xmi_type(ne)
            nname = ne.attrib.get("name", f"node_{nid}")

            kind = NODE_KIND_MAP.get(uml_type, "Node")

            incoming_ids = ne.attrib.get("incoming", "").split()
            outgoing_ids = ne.attrib.get("outgoing", "").split()

            nodes[nid] = {
                "id": nid,
                "name": nname,
                "uml_type": uml_type,
                "kind": kind,
                "activity": aid,
                "incoming_ids": incoming_ids,
                "outgoing_ids": outgoing_ids,
            }

            activities[aid]["nodes"].add(nid)

        # ------------------------------------------------------
        # 3) PARSE EDGES
        # ------------------------------------------------------
        for ee in act.findall("{*}edge"):
            eid = get_xmi_id(ee)
            uml_type = get_xmi_type(ee)
            ename = ee.attrib.get("name", f"edge_{eid}")
            kind = EDGE_KIND_MAP.get(uml_type, "ActivityEdge")

            edges[eid] = {
                "id": eid,
                "name": ename,
                "uml_type": uml_type,
                "kind": kind,
                "activity": aid,
                "source": ee.attrib.get("source"),
                "target": ee.attrib.get("target"),
            }

            activities[aid]["edges"].add(eid)

    # ------------------------------------------------------
    # RETURN STRUCTURED DATA
    # ------------------------------------------------------
    return {
        "activities": activities,
        "nodes": nodes,
        "edges": edges,
    }
