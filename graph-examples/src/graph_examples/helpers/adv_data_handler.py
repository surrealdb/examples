from graph_examples.helpers.params import DatabaseParams, SurrealParams
from graph_examples.helpers.ux_helpers import *
from surrealdb import AsyncSurreal



class ADVDataHandler():
    """
    Provides methods for managing chat sessions and messages within the application.

    This class interacts with the SurrealDB database to create, delete, load, and retrieve details
    about chat conversations and individual messages. It also integrates with the LLM handler
    to generate system messages based on user input and chat history.
    """
    def __init__(self, connection: AsyncSurreal):
        """
        Initializes the ChatHandler with a database connection.

        Args:
            connection: The SurrealDB connection object.
        """

        self.connection = connection
    

    async def get_firms(self):
        """
        Creates a new chat session in the database.

        Returns:
            dict: A dictionary containing the 'id' and 'title' of the newly created chat.
        """
        firms = await self.connection.query(
            """
                   SELECT identifier,
                    legal_name,
                    name,
                    firm_type.firm_type as firm_type,
                    city,
                    state,
                    country,
                    city,
                    postal_code,
                    chief_compliance_officer.full_name as chief_compliance_officer
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
                    firm_custodian_of.in,
                    firm_custodian_of.in.firm_type,
                    firm_custodian_of.custodian_type,
                    firm_filings,
                    firm_filings.in;
                    
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
                ->signed as signed_filings,
                ->is_compliance_officer as compliance_officer_for
                    FROM type::thing("person",[$full_name,type::thing("firm",$firm_id)])

                FETCH firm, signed_filings,compliance_officer_for;
                    
            """,
            params={"firm_id": firm_id,"full_name": full_name}
        )
        return person[0]
        