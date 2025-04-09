from graph_examples.helpers.params import DatabaseParams, SurrealParams
from graph_examples.helpers.ux_helpers import *
from surrealdb import AsyncSurreal



class ADVDataHandler():
   
    def __init__(self, connection: AsyncSurreal):
        self.connection = connection
    

    async def get_custodian_graph(self, custodian_type = None):
        surql_query = """
            SELECT *,assets_under_management,in.{name,identifier},out.{name,identifier} FROM custodian_for;
            """
        where_clause = ""
        params = {}
        if custodian_type:
            if where_clause:
                where_clause += " AND "
            where_clause += " custodian_type = type::thing('custodian_type',$custodian_type)"
            params["custodian_type"] = custodian_type

        if where_clause:
            surql_query = f"""
                SELECT *,assets_under_management,in.{{name,identifier}},out.{{name,identifier}} FROM custodian_for
                WHERE {where_clause};
            """

        graph_data = await self.connection.query(
           surql_query,params=params
        )
        return graph_data

        
    async def get_sma_graph(self):
        return self.get_custodian_graph(custodian_type = "SMA")
    

    async def get_r_b_graph(self):
        return self.get_custodian_graph(custodian_type = "A third-party unaffiliated record keeper")

        
    async def get_people(self):
       
        people = await self.connection.query(
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

    async def get_firms(self):
       
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
        Creates a new chat session in the database.

        Returns:
            dict: A dictionary containing the 'id' and 'title' of the newly created chat.
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
        Creates a new chat session in the database.

        Returns:
            dict: A dictionary containing the 'id' and 'title' of the newly created chat.
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
        Creates a new chat session in the database.

        Returns:
            dict: A dictionary containing the 'id' and 'title' of the newly created chat.
        """
        filing = await self.connection.query(
            """                                 
                                
                SELECT *,<-filed AS filed,<-signed AS signed FROM type::thing("filing",$filing_id)
                FETCH firm,signatory,execution_type,filed,signed;
                                    
            """,
            params={"filing_id": filing_id}
        )
        return filing[0]
        