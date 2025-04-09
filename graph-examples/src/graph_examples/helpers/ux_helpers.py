
from urllib.parse import quote
from surrealdb import RecordID
import datetime


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



def convert_adv_custodian_graph_to_ux_data(data):
   #SELECT description,custodian_type,assets_under_management,in.{name,identifier},out.{name,identifier} FROM custodian_for;
           
    if not data:
        return None
    
    nodes = {}
    edges = []
    edge_id_counter = 0

    node_edge_count_min = 10000000
    node_edge_count_max = 0

    for row in data:

        in_id = row["in"]["identifier"] if row["in"] else None
        out_id = row["out"]["identifier"] if row["out"] else None
        if in_id and out_id:
            if in_id not in nodes:
                node = {
                    "id": in_id,
                    "label": f"{row['in']['name']}",  
                    "edge_count": 0
                }
                nodes[in_id] = node
            else:
                nodes[in_id]["edge_count"] += 1


            if nodes[in_id]["edge_count"]>node_edge_count_max:
                node_edge_count_max = nodes[in_id]["edge_count"]
            if nodes[in_id]["edge_count"]<node_edge_count_min:
                node_edge_count_min = nodes[in_id]["edge_count"]

            if out_id not in nodes:
                
                node = {
                    "id": out_id,
                    "label": f"{row['out']['name']}",  
                    "edge_count": 0
                }
                nodes[out_id] = node
            else:
                nodes[out_id]["edge_count"] += 1

            if nodes[out_id]["edge_count"]>node_edge_count_max:
                node_edge_count_max = nodes[out_id]["edge_count"]
            if nodes[out_id]["edge_count"]<node_edge_count_min:
                node_edge_count_min = nodes[out_id]["edge_count"]


            edge_id_counter += 1

            edges.append({
                            "id": f"e{edge_id_counter}",
                            "source": row["in"]["identifier"],
                            "target": row["out"]["identifier"],
                            "label": row["custodian_type"],
                            "description": row.get("description"),  
                            "assets_under_management": row.get("assets_under_management"),
                        })

    node_edge_count_mean = edge_id_counter / len(nodes) if len(nodes)>0 else 0
    return {"nodes": list(nodes.values()), "edges": edges, 
            "node_edge_count_min":node_edge_count_min, "node_edge_count_max":node_edge_count_max ,"node_edge_count_mean":node_edge_count_mean}





def convert_corpus_graph_to_ux_data(data):
    """
    Converts your specific JSON-like data structure to Sigma.js format.

    Args:
        data: A list of dictionaries, where each dictionary represents an entity
              and its relationships.  Expected keys: 'id', 'entity_type',
              'name', 'source_document', 'relationships' (list of dicts with
              'confidence', 'relationship', 'in', 'out').

    Returns:
        A dictionary with 'nodes' and 'edges' lists, suitable for Sigma.js.
    """
    nodes = {}
    edges = []
    edge_id_counter = 0

    node_edge_count_min = 10000000
    node_edge_count_max = 0

    for edge in data:
        edge_id_counter += 1
        edges.append({
                        "id": f"e{edge_id_counter}",
                        "source": edge["in"]["identifier"],
                        "target": edge["out"]["identifier"],
                        "label": edge["relationship"],  # Relationship type
                        "confidence": edge.get("confidence", 1),  # Use .get() with default
                        # Add any other relationship properties you want here
                    })
        node_id = edge["in"]["identifier"]
        if node_id not in nodes:
            node = {
                "id": node_id,
                "label": f"{edge["in"]['name']}",  
                "entity_type": edge["in"]['entity_type'],
                "url": edge["in"]["source_document"]["url"],
                "edge_count": 1
            }
            nodes[node_id] = node
        else:
            nodes[node_id]["edge_count"] += 1

        if nodes[node_id]["edge_count"]>node_edge_count_max:
            node_edge_count_max = nodes[node_id]["edge_count"]
        if nodes[node_id]["edge_count"]<node_edge_count_min:
            node_edge_count_min = nodes[node_id]["edge_count"]
        
            
        node_id = edge["out"]["identifier"]
        if node_id not in nodes:
            node = {
                "id": node_id,
                "label": f"{edge["out"]['name']}",  
                "entity_type": edge["out"]['entity_type'],
                "url": edge["out"]["source_document"]["url"],
                "edge_count": 1
            }
            nodes[node_id] = node
        else:
            nodes[node_id]["edge_count"] += 1


        if nodes[node_id]["edge_count"]>node_edge_count_max:
            node_edge_count_max = nodes[node_id]["edge_count"]
        if nodes[node_id]["edge_count"]<node_edge_count_min:
            node_edge_count_min = nodes[node_id]["edge_count"]


    node_edge_count_mean = edge_id_counter / len(nodes) if len(nodes)>0 else 0
    return {"nodes": list(nodes.values()), "edges": edges, 
            "node_edge_count_min":node_edge_count_min, "node_edge_count_max":node_edge_count_max ,"node_edge_count_mean":node_edge_count_mean}


def organize_relations_for_ux(relations,parent_identifier):

    """
    Organizes relations data for user interface display.

    This function takes a list of relations and a parent entity identifier and restructures the data
    to group relations by the related entity. It determines the related entity (either "in" or "out")
    based on the parent identifier and creates a dictionary where keys are related entity identifiers
    and values are dictionaries containing entity information and a list of its relations to the parent.

    Args:
        relations (list): A list of relation dictionaries. Each relation dictionary is expected to
                          have "in", "out", "confidence", "relationship", "source_document", and
                          "contexts" keys. The "in" and "out" values are dictionaries containing
                          "identifier", "name", and "entity_type" keys.
        parent_identifier (str): The identifier of the parent entity for which the relations are being organized.

    Returns:
        dict: A dictionary where keys are related entity identifiers and values are dictionaries with the following structure:
              {
                  "identifier": str,
                  "name": str,
                  "entity_type": str,
                  "relations": list of dicts (each dict contains "confidence", "relationship", "source_document", "contexts")
              }
    """
    
    entity_relations_dict = {}
    for relation in relations:
        if relation["in"]["identifier"] == parent_identifier:
            entity = relation["out"]
        elif relation["in"]["identifier"] == parent_identifier:
            entity = relation["in"]
        else:
            entity = None

        if not entity is None:
            identifier = entity["identifier"]
            if identifier not in entity_relations_dict:
                entity_relations_dict[identifier] = {
                    "identifier":identifier,
                    "name":entity["name"],
                    "entity_type":entity["entity_type"],
                    "relations":[
                        {"confidence":relation["confidence"],
                        "relationship":relation["relationship"],
                        "source_document":relation["source_document"],
                        "contexts":relation["contexts"],}
                    ]
                    }
            else:
                entity_relations_dict[identifier]["relations"].append(
                    {"confidence":relation["confidence"],
                    "relationship":relation["relationship"],
                    "source_document":relation["source_document"],
                    "contexts":relation["contexts"],}
                )

    return entity_relations_dict
