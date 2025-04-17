import os
import argparse
import re


class SurrealParams():
    """
    Class to hold SurrealDB connection parameters.
    """
    def __init__(self = None, url = None,username = None, password = None, namespace = None, database = None):
        """
        Initializes SurrealDB connection parameters.

        Args:
            url (str, optional): The URL of the SurrealDB instance.
            username (str, optional): The database username.
            password (str, optional): The database password.
            namespace (str, optional): The SurrealDB namespace.
            database (str, optional): The SurrealDB database.
        """
        self.username = username
        self.password = password
        self.namespace = namespace
        self.database = database
        self.url = url

    @staticmethod
    def surql_field_name(display_name):
        """
        Generates a SurQL-compatible field name from a display name.
        """
        lower_case = display_name.lower()
        no_punctuation = re.sub(r'[^\w\s]', '', lower_case)
        snake_case = re.sub(r'\s+', '_', no_punctuation)
        return snake_case

    @staticmethod
    def ParseResponseForErrors(outcome):
      """
        Parses a SurrealDB response and raises an exception if an error is present.

        Args:
            outcome (dict): The SurrealDB response to parse.

        Returns:
            dict: The parsed response, or None if the outcome is None.

        Raises:
            SystemError: If an error is found in the response.
        """
      if outcome:
        if "result" in outcome:
            for item in outcome["result"]:
                if item["status"]=="ERR":
                    raise SystemError("Error in results: {0}".format(item["result"])) 
        
        if "error" in outcome:
            raise SystemError("Error in outcome: {0}".format(outcome["error"])) 

        return outcome
      else:
        return None
    
    
    
class DatabaseParams():
    """
    Class to hold SurrealDB connection parameters.
    """
    def __init__(self):
        """
        Initializes database connection parameters, setting up environment variable pointers.
        """
        #The path to your SurrealDB instance
        #The the SurrealDB namespace and database 
        #For use in authenticating your database
        #These are just the pointers to the env variables
        #Don't put the actual passwords here

        self.DB_USER_ENV_VAR = "SURREAL_DEMO_USER"
        self.DB_PASS_ENV_VAR = "SURREAL_DEMO_PASS"
        self.DB_URL_ENV_VAR = "SURREAL_GRAPH_DEMO_DB_URL"
        self.DB_NS_ENV_VAR = "SURREAL_GRAPH_DEMO_DB_NS"
        self.DB_DB_ENV_VAR = "SURREAL_GRAPH_DEMO_DB_DB"
    
        
        self.DB_PARAMS = SurrealParams()
                    

     
    def AddArgs(self, parser:argparse.ArgumentParser):
        """
        Adds command-line arguments for setting SurrealDB connection parameters.

        Args:
            parser (argparse.ArgumentParser): The argument parser to add arguments to.
        """
        parser.add_argument("-urlenv","--url_env", help="Your env variable for Path to your SurrealDB instance (Default: {0})".format(self.DB_URL_ENV_VAR))
        parser.add_argument("-nsenv","--namespace_env", help="Your env variable for SurrealDB namespace to create and install the data (Default: {0})".format(self.DB_NS_ENV_VAR))
        parser.add_argument("-dbenv","--database_env", help="Your env variable for SurrealDB database to create and install the data (Default: {0})".format(self.DB_DB_ENV_VAR))
        parser.add_argument("-uenv","--user_env", help="Your env variable for db username (Default: {0})".format(self.DB_USER_ENV_VAR))
        parser.add_argument("-penv","--pass_env", help="Your env variable for db password (Default: {0})".format(self.DB_PASS_ENV_VAR))


        parser.add_argument("-url","--url", help="Your Path to your SurrealDB instance (Default: {0})".format("<from env variable>"))
        parser.add_argument("-ns","--namespace", help="Your SurrealDB namespace to create and install the data (Default: {0})".format("<from env variable>"))
        parser.add_argument("-db","--database", help="Your SurrealDB database to create and install the data (Default: {0})".format("<from env variable>"))
        parser.add_argument("-u","--username", help="Your db username (Default: {0})".format("<from env variable>"))
        parser.add_argument("-p","--password", help="Your db password (Default: {0})".format("<from env variable>"))
        
    def SetArgs(self,args:argparse.Namespace):

        """
        Sets the SurrealDB connection parameters based on command-line arguments or environment variables.

        Args:
            args (argparse.Namespace): The parsed command-line arguments.
        """
        
        if args.url_env:
            self.DB_URL_ENV_VAR = args.url_env
        if args.namespace_env:
            self.DB_NS_ENV_VAR = args.namespace_env
        if args.database_env:
            self.DB_DB_ENV_VAR = args.database_env
        if args.user_env:
            self.DB_USER_ENV_VAR = args.user_env
        if args.pass_env:
            self.DB_PASS_ENV_VAR = args.pass_env

        if args.url:
            self.DB_PARAMS.url = args.url
        else:
            self.DB_PARAMS.url = os.getenv(self.DB_URL_ENV_VAR)

        if args.namespace:
            self.DB_PARAMS.namespace = args.namespace
        else:
            self.DB_PARAMS.namespace = os.getenv(self.DB_NS_ENV_VAR)

        if args.database:
            self.DB_PARAMS.database = args.database
        else:
            self.DB_PARAMS.database = os.getenv(self.DB_DB_ENV_VAR)

        if args.username:
            self.DB_PARAMS.username = args.username
        else:
            self.DB_PARAMS.username = os.getenv(self.DB_USER_ENV_VAR)

        if args.password:
            self.DB_PARAMS.password = args.password
        else:
            self.DB_PARAMS.password = os.getenv(self.DB_PASS_ENV_VAR)

        
    


       
        