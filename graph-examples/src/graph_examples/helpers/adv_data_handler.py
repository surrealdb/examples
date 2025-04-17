from graph_examples.helpers.params import DatabaseParams, SurrealParams
from graph_examples.helpers.ux_helpers import *
from surrealdb import AsyncSurreal



class ADVDataHandler():
    """
    This class provides methods to interact with the SurrealDB database
    for retrieving and manipulating data related to ADV filings.

    It encapsulates various queries and data retrieval operations,
    making it easier to access and present ADV data in a user-friendly format.
    """
   
    def __init__(self, connection: AsyncSurreal):
        self.connection = connection
    



    async def get_custodian_graph(self, custodian_type:str = None, 
                                  description_matches:list[str] = None, 
                                  order_by:str = None,
                                  filing_id:int = None,
                                  firm_id:int = None,
                                  person_filter:str = None,
                                  firm_type:str =None,
                                  firm_filter:str =None,
                                  limit:int = None,
                                  ):
        
        """
        Retrieves graph data about custodians and their relationships.

        This method constructs a SurrealQL query to select custodian relationships
        and associated firm information, allowing for various filtering and ordering
        options.

        Args:
            custodian_type: Optional. Filters results by custodian type (e.g., "RAUM").
            description_matches: Optional. Filters results based on matches in the custodian's description.
            order_by: Optional. Specifies the field to order the results by.
            filing_id: Optional. Filters results by the filing ID.
            firm_id: Optional. Filters results by the firm ID.
            person_filter: Optional. Filters results based on related persons.
            firm_type: Optional. Filters results by firm type.
            firm_filter: Optional. Filters results based on firm name or identifiers.
            limit: Optional. Limits the number of results returned.

        Returns:
            A list of dictionaries, where each dictionary represents a custodian relationship
            and includes details about the related firms.
        """
        
        where_clause = ""
        pre_query_clause = ""
        params = {}
        result_index = 0
        if filing_id:
            where_clause += " source_filing = type::thing('filing',$filing_id)"
            params["filing_id"] = filing_id
        
        if firm_id:
            where_clause += " (in.id = type::thing('firm',$firm_id) OR out.id = type::thing('firm',$firm_id))"
            params["firm_id"] = firm_id

        if custodian_type:
            if where_clause:
                where_clause += " AND "
            where_clause += " custodian_type = type::thing('custodian_type',$custodian_type)"
            params["custodian_type"] = custodian_type

        if firm_type:
            if where_clause:
                where_clause += " AND "
            where_clause += "( in.firm_type = type::thing('firm_type',$firm_type) OR out.firm_type = type::thing('firm_type',$firm_type) )"
            params["firm_type"] = firm_type
        

        if description_matches:
            if where_clause:
                where_clause += " AND ("
            match_index = 1
            where_clause += f"description @{match_index}@ $description_matches[0]"
            for match in description_matches[1:]:
                match_index += 1
                where_clause += f" OR description @{match_index}@ $description_matches[{match_index}]"
            where_clause += ")"
            params["description_matches"] = description_matches


        if firm_filter:
            if where_clause:
                where_clause += " AND "
            where_clause += "( in.name @@ $firm_filter OR out.name @@ $firm_filter )"
            params["firm_filter"] = firm_filter
        
        if firm_filter:
            result_index += 1
            if where_clause:
                where_clause += " AND "
            pre_query_clause += f"""
                
                LET $firm_list = array::group( SELECT VALUE firm.id FROM firm_alias 
                                WHERE 
                                name @@ $firm_filter OR
                                legal_name @@ $firm_filter OR 
                                sec_number = $firm_filter OR 
                                (cik IS NOT NONE AND <string>cik = $firm_filter) OR 
                                pfid = $firm_filter OR 
                                legal_entity_identifier = $firm_filter 
                                );
            """
            where_clause += f" in IN $firm_list OR out in $firm_list"
            params["firm_filter"] = firm_filter


        if person_filter:
            result_index += 1
            if where_clause:
                where_clause += " AND "
            pre_query_clause += f"""
                LET $person_firm_list = array::group( SELECT VALUE person->signed->filing.firm FROM person_alias 
                WHERE 
                full_name = $person_filter OR full_name @@ $person_filter OR
                title = $person_filter OR title @@ $person_filter
                );
            """
            where_clause += f" in IN $person_firm_list OR out in $person_firm_list"
            params["person_filter"] = person_filter


        surql_query = pre_query_clause + """
        SELECT id,description,custodian_type.custodian_type AS custodian_type,assets_under_management,
        in.{name,identifier,firm_type,section_5f},
        out.{name,identifier,firm_type,section_5f} FROM custodian_for
        """
        
        if where_clause:
            surql_query += f"""
                WHERE {where_clause}
            """
        if order_by:
            surql_query += f"""
                ORDER BY {order_by}
            """
        if limit:
            surql_query += f"""
                LIMIT {limit}
            """
        

        graph_data =  SurrealParams.ParseResponseForErrors(await self.connection.query_raw(
           surql_query,params=params
        ))
        return graph_data["result"][result_index]["result"]

        
    async def get_raum_graph(self):
        """
        Retrieves graph data specifically for RAUM (Reporting Agent Under Management) custodians.

        Returns:
            A list of dictionaries representing RAUM custodian relationships.
        """
        return self.get_custodian_graph(custodian_type = "RAUM")
    

    async def get_cloud_graph(self):
        """
        Retrieves graph data specifically for custodians related to "cloud" and "data".

        Returns:
            A list of dictionaries representing custodian relationships related to cloud and data.
        """
        return self.get_custodian_graph(custodian_type = "A third-party unaffiliated record keeper",description_matches = ["cloud","data"])

        
    async def get_people(self):
        """
        Retrieves information about people (e.g., officers) associated with firms.

        Returns:
            A list of dictionaries, where each dictionary represents a person
            and includes their details and firm affiliations.
        """
        people =  await self.connection.query(
            """  
            SELECT 
                first_name,
                last_name,
                full_name ,
                title,
                firm.{identifier,name},
                ->is_compliance_officer.{as_of_latest_filing_date,title_at_time_of_filing} as is_compliance_officer
                FROM person;
                """
        )
        return people
    

    async def get_filings(self):
        """
        Retrieves information about filings (e.g., ADV filings).

        Returns:
            A list of dictionaries, where each dictionary represents a filing
            and includes details about the firm, signatory, and execution type.
        """
       
        filings = await self.connection.query(
            """  
            SELECT 
            filing_id,  
            execution_type.execution_type AS execution_type,
            firm.{name,identifier},
            signatory.{full_name,title},
            <-signed.execution_date[0] AS execution_date 
            FROM filing;"""
        )
        return filings




    async def hedge_custodian_report(self):
        """
        Generates a report on hedge fund custodians, ordered by assets under management.

        Returns:
            A list of dictionaries, where each dictionary represents a hedge fund
            and includes information about its custodians and total assets under management.
        """
       
        report_data = await self.connection.query(
            """
                 SELECT id,identifier,firm_type,name, customers.{name,id,identifier} AS customers, math::sum(assets_under_management)  AS assets_under_management FROM 
                (
                    SELECT id,identifier,firm_type,name,->custodian_for.out AS customers, ->custodian_for.assets_under_management.map(|$v| IF $v IS NONE THEN 0 ELSE $v END) AS assets_under_management  
                    FROM firm 
                    WHERE firm_type = type::thing("firm_type",$firm_type) 
                )
                ORDER BY assets_under_management DESC
                ;

            """, params = {"firm_type": "Hedge Fund"}
        )
        return report_data
    

    async def vc_custodian_report(self):
        """
        Generates a report on hedge fund custodians, ordered by assets under management.

        Returns:
            A list of dictionaries, where each dictionary represents a hedge fund
            and includes information about its custodians and total assets under management.
        """
       
        report_data = await self.connection.query(
            """
                 SELECT id,identifier,firm_type,name, customers.{name,id,identifier} AS customers, math::sum(assets_under_management)  AS assets_under_management FROM 
                (
                    SELECT id,identifier,firm_type,name,->custodian_for.out AS customers, ->custodian_for.assets_under_management.map(|$v| IF $v IS NONE THEN 0 ELSE $v END) AS assets_under_management  
                    FROM firm 
                    WHERE firm_type = type::thing("firm_type",$firm_type) 
                )
                ORDER BY assets_under_management DESC
                ;

            """, params = {"firm_type": "Venture Capital Fund"}
        )
        return report_data


    async def get_firms(self):
        """
        Generates a report on hedge fund custodians, ordered by assets under management.

        Returns:
            A list of dictionaries, where each dictionary represents a hedge fund
            and includes information about its custodians and total assets under management.
        """
       
        firms = await self.connection.query(
            """
                   SELECT identifier,
                    legal_name,
                    name,
                    firm_type.firm_type AS firm_type,
                    city,
                    state,
                    country,
                    city,
                    postal_code,
                    chief_compliance_officer.full_name AS chief_compliance_officer
                    FROM firm;"""
        )
        return firms
        
    async def get_firm(self,firm_id):
        """
        Generates a report on hedge fund custodians, ordered by assets under management.

        Returns:
            A list of dictionaries, where each dictionary represents a hedge fund
            and includes information about its custodians and total assets under management.
        """
        firm = await self.connection.query(
            """                                 
                
                SELECT 
                *,
                <-custodian_for.* AS firm_custodians,
                ->custodian_for.* AS firm_custodian_of,
                ->filed->filing<-signed AS firm_filings
                FROM type::thing("firm",$firm_id)
                FETCH chief_compliance_officer,
                    firm_type,
                    firm_custodians.in,
                    firm_custodians.in.firm_type,
                    firm_custodians.custodian_type,
                    firm_custodian_of.out,
                    firm_custodian_of.out.firm_type,
                    firm_custodian_of.custodian_type,
                    firm_filings,
                    firm_filings.in,
                    firm_filings.out;
                    
            """,
            params={"firm_id": firm_id}
        )
        return firm[0]
        
    async def get_person(self,firm_id,full_name):
        """
        Retrieves detailed information about a specific person associated with a firm.

        Args:
            firm_id: The identifier of the firm the person is associated with.
            full_name: The full name of the person to retrieve.

        Returns:
            A dictionary containing detailed information about the person,
            including related entities like signed filings and compliance officer roles.
        """
        person = await self.connection.query(
            """                                 
                
                            
                SELECT 
                    *,
                ->signed AS signed_filings,
                ->is_compliance_officer AS compliance_officer_for
                    FROM type::thing("person",[$full_name,type::thing("firm",$firm_id)])

                FETCH firm, signed_filings,compliance_officer_for,signed_filings.out,signed_filings.out.execution_type;
                    
            """,
            params={"firm_id": firm_id,"full_name": full_name}
        )
        return person[0]
        
    async def get_filing(self,filing_id):
        """
        Retrieves detailed information about a specific filing.

        Args:
            filing_id: The identifier of the filing to retrieve.

        Returns:
            A dictionary containing detailed information about the filing,
            including related entities like firm, signatory, and execution type.
        """
        filing = await self.connection.query(
            """                                 
                                
                SELECT *,<-filed AS filed,<-signed AS signed FROM type::thing("filing",$filing_id)
                FETCH firm,signatory,execution_type,filed,signed;
                                    
            """,
            params={"filing_id": filing_id}
        )
        return filing[0]
        