
from urllib.parse import quote
from surrealdb import RecordID
import datetime

from typing import Dict, List, Any, Optional


"""Format a SurrealDB RecordID for use in a URL.

    Replaces '/' with '|' and URL-encodes the ID.

    Args:
        surrealdb_id: SurrealDB RecordID.

    Returns:
        Formatted string for use in a URL.
    """
def format_url_id(surrealdb_id: RecordID) -> str:

    if RecordID == type(surrealdb_id):
        str_to_format = surrealdb_id.id
    else:
        str_to_format = surrealdb_id
    return quote(str_to_format).replace("/","|")
    
"""Unformat a URL-encoded SurrealDB RecordID.

    Replaces '|' with '/'.

    Args:
        surrealdb_id: URL-encoded SurrealDB RecordID.

    Returns:
        Unformatted string.
    """
def unformat_url_id(surrealdb_id: str) -> str:
    return surrealdb_id.replace("|","/")




"""Extract numeric ID from SurrealDB record ID.

    SurrealDB record ID comes in the form of `<table_name>:<unique_id>`.
    CSS classes cannot be named with a `:` so for CSS we extract the ID.

    Args:
        surrealdb_id: SurrealDB record ID.

    Returns:
        ID with ':' replaced by '-'.
    """
def extract_id(surrealdb_id) -> str:
    
    if RecordID == type(surrealdb_id):
    #return surrealdb_id.id
        return surrealdb_id.id.replace(":","-")
    else:
        return surrealdb_id.replace(":","-")


"""Convert a SurrealDB `datetime` to a readable string.

    Args:
        timestamp: SurrealDB `datetime` value.

    Returns:
        Date as a string.
    """
def convert_timestamp_to_date(timestamp: str) -> str:
    
    # parsed_timestamp = datetime.datetime.fromisoformat(timestamp.rstrip("Z"))
    # return parsed_timestamp.strftime("%B %d %Y, %H:%M")
    return timestamp

def format_value(value):
    """Formats a value for display based on its type."""
    if isinstance(value, float):
        return "{:,.2f}".format(value)
    elif isinstance(value, int):
        return "{:,}".format(value)
    elif isinstance(value, datetime.datetime):
        return value.strftime("%Y-%m-%d")
    return str(value)

def extract_field_value(data, field_name):
    """
    Extracts the value of a specific field from a dictionary, handling dot notation.

    Args:
        data: The dictionary to extract the value from.
        field_name: The name of the field to extract (can use dot notation).

    Returns:
        The value of the specified field, or None if any part of the path is missing or data is not a dict.
    """
    if not isinstance(data, dict) or not field_name:
        return None

    parts = field_name.split('.')
    current_level = data

    for part in parts:
        if isinstance(current_level, dict) and part in current_level:
            current_level = current_level[part]
        else:
            return None  # Return None if the path doesn't exist

    return format_value(current_level)



def convert_adv_custodian_graph_to_ux_data(
    data: List[Dict[str, Any]],
    source_node_weight_field: Optional[str],
    target_node_weight_field: Optional[str],
    edge_weight_field: Optional[str],
    use_parent_aggregation: Optional[bool] = False,
) -> Optional[Dict[str, Any]]:
    """
    Transforms data retrieved from a SurrealDB graph query about ADV custodians
    into a format suitable for user interface (UX) visualization.

    The function processes a list of rows, where each row represents a custodian
    relationship between two firms. It extracts node (firm) and edge (relationship)
    information, calculates weight ranges for nodes and edges, and formats the data
    into a dictionary containing nodes, edges, and weight range metadata.

    Args:
        data: A list of dictionaries, where each dictionary represents a row
              from a SurrealDB query. Each row is expected to have a specific
              structure (see example query in docstring).
        source_node_weight_field: Optional. The name of the field in the 'in' node
                                  to use for calculating source node weight ranges.
        target_node_weight_field: Optional. The name of the field in the 'out' node
                                  to use for calculating target node weight ranges.
        edge_weight_field: Optional. The name of the field in the edge data to use
                          for calculating edge weight ranges.

    Returns:
        A dictionary containing the transformed data, or None if the input data is empty.
        The dictionary has the following structure:
        {
            "nodes": List of node dictionaries,
            "edges": List of edge dictionaries,
            "source_node_weight_min": Minimum source node weight (or inf if no weights),
            "source_node_weight_max": Maximum source node weight (or -inf if no weights),
            "target_node_weight_min": Minimum target node weight (or inf if no weights),
            "target_node_weight_max": Maximum target node weight (or -inf if no weights),
            "edge_weight_min": Minimum edge weight (or inf if no weights),
            "edge_weight_max": Maximum edge weight (or -inf if no weights)
        }

    Example SurrealDB query (illustrative):
        SELECT id, description, custodian_type.custodian_type AS custodian_type,
               assets_under_management,
               in.{name, identifier, firm_type, section_5f},
               out.{name, identifier, firm_type, section_5f}
        FROM custodian_for
    """

    if not data:
        return None
    
    nodes = {}
    edges = {}
    edge_id_counter = 0

    source_node_weight_min = float("inf")
    source_node_weight_max = -source_node_weight_min
    target_node_weight_min = float("inf")
    target_node_weight_max = -target_node_weight_min


    edge_weight_min = float("inf")
    edge_weight_max = -edge_weight_min

    for row in data:
        in_id = None
        out_id = None
        in_name = None
        out_name = None
        if use_parent_aggregation:
            in_id = "p:" + row["in"]["parent_firm"].id if row["in"] else None
            out_id = "p:" + row["out"]["parent_firm"].id if row["out"] else None
            in_name = row["in"]["parent_firm"].id
            out_name = row["out"]["parent_firm"].id
            
        else:
            in_id = row["in"]["identifier"] if row["in"] else None
            out_id = row["out"]["identifier"] if row["out"] else None
            in_name = row['in']['name']
            out_name = row['out']['name']

        
        if in_id and out_id:
            if in_id not in nodes:
                node = {
                    "id": in_id,
                    "name": in_name, 
                    "firm_type": row["in"]["firm_type"].id, 
                    "edge_count": 0,
                    "total_assets": row["in"]["section_5f"].get("total_regulatory_assets") if ("section_5f" in row["in"] and row["in"]["section_5f"]) else None,
                    "assets_under_management": 0 if row.get("assets_under_management") is None else row.get("assets_under_management"),
                    "is_source": True,
                }
                nodes[in_id] = node
            else:
                nodes[in_id]["edge_count"] += 1
                if use_parent_aggregation:
                    nodes[in_id]["assets_under_management"] += 0 if row.get("assets_under_management") is None else row.get("assets_under_management")

            node_weight = nodes[in_id].get(source_node_weight_field)
            if node_weight is not None:
                if node_weight > source_node_weight_max:
                    source_node_weight_max = node_weight
                if node_weight < source_node_weight_min:
                    source_node_weight_min = node_weight

            if out_id not in nodes:
                node = {
                    "id": out_id,
                    "name": out_name,  
                    "firm_type": row["out"]["firm_type"].id, 
                    "edge_count": 0,
                    "total_assets": row["out"]["section_5f"].get("total_regulatory_assets") if ("section_5f" in row["out"] and row["out"]["section_5f"]) else None,
                    "assets_under_management": 0 if row.get("assets_under_management") is None else row.get("assets_under_management"),
                    "is_source": False,
                }
                nodes[out_id] = node
            else:
                nodes[out_id]["edge_count"] += 1
                if use_parent_aggregation:
                    nodes[out_id]["assets_under_management"] += 0 if row.get("assets_under_management") is None else row.get("assets_under_management")

            
            node_weight = nodes[out_id].get(target_node_weight_field)
            if node_weight is not None:
                if node_weight > target_node_weight_max:
                    target_node_weight_max = node_weight
                if node_weight < target_node_weight_min:
                    target_node_weight_min = node_weight


            edge_id_counter += 1
            edge_id = None
            edge = None
            if use_parent_aggregation:
                edge_id = f"{in_id},{out_id},{row["custodian_type"]}"
                if edge_id not in edges:
                    edge = {
                            "id": edge_id,
                            "source": in_id,
                            "target": out_id,
                            "custodian_type": row["custodian_type"],
                            "description": "" if row.get("description") is None else row.get("description") ,  
                            "assets_under_management": 0 if row.get("assets_under_management") is None else row.get("assets_under_management"),
                        }
                else:   
                    edge = edges[edge_id]
                    edge["description"] += "" if row.get("description") is None else row.get("description") 
                    edge["assets_under_management"] += 0 if row.get("assets_under_management") is None else row.get("assets_under_management") 

            else:
                edge_id = f"{row["id"].id}"
                edge = {
                        "id": edge_id,
                        "source": in_id,
                        "target": out_id,
                        "custodian_type": row["custodian_type"],
                        "description": row.get("description"),  
                        "assets_under_management":  0 if row.get("assets_under_management") is None else row.get("assets_under_management"),
                    }
                  

            if edge_weight_field:
                edge_weight = row.get(edge_weight_field)
                if edge_weight is not None:     
                    if edge_weight > edge_weight_max:
                        edge_weight_max = edge_weight
                    if edge_weight < edge_weight_min:
                        edge_weight_min = edge_weight

            edges[edge_id] = edge
                

    return {"nodes": list(nodes.values()), "edges": list(edges.values()), 
            "source_node_weight_min":source_node_weight_min, "source_node_weight_max":source_node_weight_max, 
            "target_node_weight_min":target_node_weight_min, "target_node_weight_max":target_node_weight_max, 
            "edge_weight_min":edge_weight_min, "edge_weight_max":edge_weight_max }

