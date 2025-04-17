/*
This file defines the SurrealQL for this project.
*/

// Defines a custom analyzer named 'snowball_analyzer' for text searching.
// It uses the 'class' tokenizer (which tokenizes based on word boundaries)
// and applies two filters:
// 1. 'lowercase': Converts all tokens to lowercase for case-insensitive searching.
// 2. 'snowball(english)': Applies the Snowball stemming algorithm for English,
//    reducing words to their root form to improve search recall.
DEFINE ANALYZER IF NOT EXISTS snowball_analyzer
    TOKENIZERS class
    FILTERS lowercase, snowball(english);

// Defines another custom analyzer named 'name_analyzer' specifically for names.
// It uses the 'class' tokenizer and applies these filters:
// 1. 'lowercase': Converts tokens to lowercase.
// 2. 'ascii': Removes any non-ASCII characters.
// 3. 'ngram(2, 10)': Creates n-grams (sequences of characters) of length 2 to 10.
//    This is useful for partial name matching and handling typos.
DEFINE ANALYZER OVERWRITE name_analyzer TOKENIZERS
    class FILTERS lowercase, ascii, ngram(2, 10);


DEFINE TABLE IF NOT EXISTS firm_type SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS firm_type ON TABLE firm_type TYPE string;
UPSERT firm_type:`ERA` CONTENT{
    firm_type : 'ERA'};
UPSERT firm_type:`Registered` CONTENT{
    firm_type : 'Registered'};
UPSERT firm_type:`Records Custodian` CONTENT{
    firm_type : 'Records Custodian'};
UPSERT firm_type:`RAUM Custodian` CONTENT{
    firm_type : 'RAUM Custodian'};
UPSERT firm_type:`PF Custodian` CONTENT{
    firm_type : 'PF Custodian'};






DEFINE TABLE IF NOT EXISTS firm SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS name ON TABLE firm TYPE string;
DEFINE FIELD IF NOT EXISTS identifier ON TABLE firm TYPE string;
DEFINE FIELD IF NOT EXISTS firm_type ON TABLE firm TYPE Record<firm_type>;
DEFINE FIELD IF NOT EXISTS legal_name ON TABLE firm TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS city ON TABLE firm TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS state ON TABLE firm TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS country ON TABLE firm TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS postal_code ON TABLE firm TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS chief_compliance_officer ON TABLE firm TYPE Option<Record<person>>;
DEFINE FIELD IF NOT EXISTS firm_aliases ON TABLE firm TYPE Option<Array<Record<firm_alias>>>;


-- Define fields for section1
DEFINE FIELD IF NOT EXISTS section1 ON TABLE firm TYPE Option<object>;
DEFINE FIELD IF NOT EXISTS section1.sec_region ON TABLE firm TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS section1.organization_crd ON TABLE firm TYPE Option<int>;
DEFINE FIELD IF NOT EXISTS section1.firm_type ON TABLE firm TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS section1.cik ON TABLE firm TYPE Option<int>;
DEFINE FIELD IF NOT EXISTS section1.primary_business_name ON TABLE firm TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS section1.legal_name ON TABLE firm TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS section1.main_office_street_address_1 ON TABLE firm TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS section1.main_office_street_address_2 ON TABLE firm TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS section1.main_office_city ON TABLE firm TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS section1.main_office_state ON TABLE firm TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS section1.main_office_country ON TABLE firm TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS section1.main_office_postal_code ON TABLE firm TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS section1.chief_compliance_officer_name ON TABLE firm TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS section1.chief_compliance_officer_other_titles ON TABLE firm TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS section1.chief_compliance_officer_e_mail ON TABLE firm TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS section1.latest_adv_filing_date ON TABLE firm TYPE Option<datetime>;
DEFINE FIELD IF NOT EXISTS section1.website_address ON TABLE firm TYPE Option<string>;
-- Define fields for section_5d
DEFINE FIELD IF NOT EXISTS section_5d ON TABLE firm TYPE Option<object>;
DEFINE FIELD IF NOT EXISTS section_5d.approx_amount_of_assets ON TABLE firm TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS section_5d.individuals_other_than_high_net_worth_number_of_clients ON TABLE firm TYPE Option<int>;
DEFINE FIELD IF NOT EXISTS section_5d.individuals_other_than_high_net_worth_regulatory_assets ON TABLE firm TYPE Option<float>;
DEFINE FIELD IF NOT EXISTS section_5d.high_net_worth_individuals_number_of_clients ON TABLE firm TYPE Option<int>;
DEFINE FIELD IF NOT EXISTS section_5d.high_net_worth_individuals_regulatory_assets ON TABLE firm TYPE Option<float>;
DEFINE FIELD IF NOT EXISTS section_5d.banking_or_thrift_institutions_number_of_clients ON TABLE firm TYPE Option<int>;
DEFINE FIELD IF NOT EXISTS section_5d.banking_or_thrift_institutions_regulatory_assets ON TABLE firm TYPE Option<float>;
DEFINE FIELD IF NOT EXISTS section_5d.investment_companies_number_of_clients ON TABLE firm TYPE Option<int>;
DEFINE FIELD IF NOT EXISTS section_5d.investment_companies_regulatory_assets ON TABLE firm TYPE Option<float>;
DEFINE FIELD IF NOT EXISTS section_5d.business_development_companies_number_of_clients ON TABLE firm TYPE Option<int>;
DEFINE FIELD IF NOT EXISTS section_5d.business_development_companies_regulatory_assets ON TABLE firm TYPE Option<float>;
DEFINE FIELD IF NOT EXISTS section_5d.pooled_investment_vehicles_number_of_clients ON TABLE firm TYPE Option<int>;
DEFINE FIELD IF NOT EXISTS section_5d.pooled_investment_vehicles_regulatory_assets ON TABLE firm TYPE Option<float>;
DEFINE FIELD IF NOT EXISTS section_5d.pension_and_profit_sharing_plans_number_of_clients ON TABLE firm TYPE Option<int>;
DEFINE FIELD IF NOT EXISTS section_5d.pension_and_profit_sharing_plans_regulatory_assets ON TABLE firm TYPE Option<float>;
DEFINE FIELD IF NOT EXISTS section_5d.charitable_organizations_number_of_clients ON TABLE firm TYPE Option<int>;
DEFINE FIELD IF NOT EXISTS section_5d.charitable_organizations_regulatory_assets ON TABLE firm TYPE Option<float>;
DEFINE FIELD IF NOT EXISTS section_5d.state_or_municipal_government_entities_number_of_clients ON TABLE firm TYPE Option<int>;
DEFINE FIELD IF NOT EXISTS section_5d.state_or_municipal_government_entities_regulatory_assets ON TABLE firm TYPE Option<float>;
DEFINE FIELD IF NOT EXISTS section_5d.other_investment_advisers_number_of_clients ON TABLE firm TYPE Option<int>;
DEFINE FIELD IF NOT EXISTS section_5d.other_investment_advisers_regulatory_assets ON TABLE firm TYPE Option<float>;
DEFINE FIELD IF NOT EXISTS section_5d.insurance_companies_number_of_clients ON TABLE firm TYPE Option<int>;
DEFINE FIELD IF NOT EXISTS section_5d.insurance_companies_regulatory_assets ON TABLE firm TYPE Option<float>;
DEFINE FIELD IF NOT EXISTS section_5d.sovereign_wealth_funds_number_of_clients ON TABLE firm TYPE Option<int>;
DEFINE FIELD IF NOT EXISTS section_5d.sovereign_wealth_funds_regulatory_assets ON TABLE firm TYPE Option<float>;
DEFINE FIELD IF NOT EXISTS section_5d.corporations_or_other_businesses_number_of_clients ON TABLE firm TYPE Option<int>;
DEFINE FIELD IF NOT EXISTS section_5d.corporations_or_other_businesses_regulatory_assets ON TABLE firm TYPE Option<float>;
DEFINE FIELD IF NOT EXISTS section_5d.other_number_of_clients ON TABLE firm TYPE Option<int>;
DEFINE FIELD IF NOT EXISTS section_5d.other_regulatory_assets ON TABLE firm TYPE Option<float>;
DEFINE FIELD IF NOT EXISTS section_5d.other_details ON TABLE firm TYPE Option<string>;

-- Define fields for section_5f
DEFINE FIELD IF NOT EXISTS section_5f ON TABLE firm TYPE Option<object>;
DEFINE FIELD IF NOT EXISTS section_5f.discretionary_regulatory_assets ON TABLE firm TYPE Option<float>;
DEFINE FIELD IF NOT EXISTS section_5f.nondiscretionary_regulatory_assets ON TABLE firm TYPE Option<float>;
DEFINE FIELD IF NOT EXISTS section_5f.total_regulatory_assets ON TABLE firm TYPE Option<float>;
DEFINE FIELD IF NOT EXISTS section_5f.discretionary_accounts ON TABLE firm TYPE Option<int>;
DEFINE FIELD IF NOT EXISTS section_5f.nondiscretionary_accounts ON TABLE firm TYPE Option<int>;
DEFINE FIELD IF NOT EXISTS section_5f.total_accounts ON TABLE firm TYPE Option<int>;
DEFINE FIELD IF NOT EXISTS section_5f.nonus_regulatory_assets ON TABLE firm TYPE Option<float>;




// Defines an index named 'name_text_index' on the 'firm' table for the 'name' field.
// It uses the 'name_analyzer' for text searching and the BM25 ranking algorithm.
DEFINE INDEX IF NOT EXISTS name_text_index ON TABLE firm
    FIELDS name SEARCH ANALYZER name_analyzer BM25;

// Defines an index for the 'legal_name' field on the 'firm' table, using 'name_analyzer'.
DEFINE INDEX IF NOT EXISTS legal_name_text_index ON TABLE firm
    FIELDS legal_name SEARCH ANALYZER name_analyzer BM25;

// Defines a regular index on the 'identifier' field of the 'firm' table for exact lookups.
DEFINE INDEX IF NOT EXISTS identifier_index ON TABLE firm
    FIELDS identifier;

// Defines a regular index on the 'cik' field within the 'section1' object of the 'firm' table.
DEFINE INDEX IF NOT EXISTS cik_index ON firm
    FIELDS section1.cik;

// Defines a regular index on the 'firm_type.firm_type' field of the 'firm' table.
DEFINE INDEX IF NOT EXISTS firm_type_index ON firm
    FIELDS firm_type.firm_type;


DEFINE TABLE IF NOT EXISTS firm_alias SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS firm ON TABLE firm_alias TYPE Record<firm>;
DEFINE FIELD IF NOT EXISTS name ON TABLE firm_alias TYPE string;
DEFINE FIELD IF NOT EXISTS legal_name ON TABLE firm_alias TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS sec_number ON TABLE firm_alias TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS legal_entity_identifier ON TABLE firm_alias TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS cik ON TABLE firm_alias TYPE Option<int>;
DEFINE FIELD IF NOT EXISTS firm_type ON TABLE firm_alias TYPE Record<firm_type>;
DEFINE FIELD IF NOT EXISTS city ON TABLE firm_alias TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS state ON TABLE firm_alias TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS country ON TABLE firm_alias TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS postal_code ON TABLE firm_alias TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS source_filing ON TABLE firm_alias TYPE Option<Record<filing>>;
DEFINE FIELD IF NOT EXISTS pfid ON TABLE firm_alias TYPE Option<string>;

// Defines text search indexes for 'name' and 'legal_name' on the 'firm_alias' table.
DEFINE INDEX IF NOT EXISTS name_text_index ON TABLE firm_alias
    FIELDS name SEARCH ANALYZER name_analyzer BM25;

DEFINE INDEX IF NOT EXISTS legal_name_text_index ON TABLE firm_alias
    FIELDS legal_name SEARCH ANALYZER name_analyzer BM25;




// Defines a RELATION table named 'signed' between 'person' and 'filing'.
DEFINE TABLE IF NOT EXISTS signed TYPE RELATION
IN person OUT filing SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS execution_date ON TABLE signed TYPE datetime;
DEFINE FIELD IF NOT EXISTS signatory_title ON TABLE signed TYPE Option<string>;

// Defines a RELATION table named 'is_compliance_officer' between 'person' and 'firm'.
DEFINE TABLE IF NOT EXISTS is_compliance_officer TYPE RELATION
IN person OUT firm SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS as_of_latest_filing_date ON TABLE is_compliance_officer TYPE datetime;
DEFINE FIELD IF NOT EXISTS title_at_time_of_filing ON TABLE is_compliance_officer TYPE Option<string>;

// Defines a RELATION table named 'custodian_for' between two 'firm' records.
DEFINE TABLE IF NOT EXISTS custodian_for TYPE RELATION
IN firm OUT firm SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS source_filing ON TABLE custodian_for TYPE Record<filing>;
DEFINE FIELD IF NOT EXISTS custodian_type ON TABLE custodian_for TYPE Record<custodian_type>;
DEFINE FIELD IF NOT EXISTS legal_entity_identifier ON TABLE custodian_for TYPE Option<string>;

DEFINE FIELD IF NOT EXISTS description ON TABLE custodian_for TYPE Option<string>;

DEFINE FIELD IF NOT EXISTS assets_under_management ON TABLE custodian_for TYPE Option<float>;
DEFINE FIELD IF NOT EXISTS related_person ON TABLE custodian_for TYPE Option<bool>;

DEFINE FIELD IF NOT EXISTS section_d_7b1 ON TABLE custodian_for TYPE Option<object>;

DEFINE FIELD IF NOT EXISTS section_d_7b1.percentage_owned_you_or_related ON TABLE custodian_for TYPE Option<float>;
DEFINE FIELD IF NOT EXISTS section_d_7b1.percentage_owned_funds ON TABLE custodian_for TYPE Option<float>;
DEFINE FIELD IF NOT EXISTS section_d_7b1.percentage_invested ON TABLE custodian_for TYPE Option<float>;
DEFINE FIELD IF NOT EXISTS section_d_7b1.unqualified_opinion ON TABLE custodian_for TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS section_d_7b1.fund_type_other ON TABLE custodian_for TYPE Option<string>;

// Defines a text search index on the 'description' field of the 'custodian_for' table.
DEFINE INDEX IF NOT EXISTS description_index ON TABLE custodian_for
    FIELDS description SEARCH ANALYZER snowball_analyzer BM25;



// Defines a RELATION table named 'master_of_feeder' between two 'firm' records.
DEFINE TABLE IF NOT EXISTS master_of_feeder TYPE RELATION
IN firm OUT firm SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS source_filing ON TABLE master_of_feeder TYPE Record<filing>;
DEFINE FIELD IF NOT EXISTS master_fund_name ON TABLE master_of_feeder TYPE Option<string>;

           




DEFINE TABLE IF NOT EXISTS filing SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS filing_id ON TABLE filing TYPE int;
DEFINE FIELD IF NOT EXISTS firm ON TABLE filing TYPE Record<firm>;
DEFINE FIELD IF NOT EXISTS execution_type ON TABLE filing TYPE Record<ia_filing_execution_type>;
DEFINE FIELD IF NOT EXISTS signatory ON TABLE filing TYPE Record<person>;

// Defines a RELATION table named 'filed' between 'firm' and 'filing'.
DEFINE TABLE IF NOT EXISTS filed TYPE RELATION
IN firm OUT filing SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS execution_date ON TABLE filed TYPE datetime;

// Defines a table named 'ia_filing_execution_type' with SCHEMAFULL mode.
DEFINE TABLE IF NOT EXISTS ia_filing_execution_type SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS execution_type ON TABLE ia_filing_execution_type TYPE string;

// Defines a table named 'custodian_type' with SCHEMAFULL mode.
DEFINE TABLE IF NOT EXISTS custodian_type SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS custodian_type ON TABLE custodian_type TYPE string;
// Inserts or updates records in the 'custodian_type' table.
UPSERT custodian_type:`RAUM` CONTENT{
    custodian_type : 'RAUM'};
UPSERT custodian_type:`PF` CONTENT{
custodian_type : 'PF'};



DEFINE TABLE IF NOT EXISTS person SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS full_name ON TABLE person TYPE string;
DEFINE FIELD IF NOT EXISTS firm ON TABLE person TYPE Record<firm>;
DEFINE FIELD IF NOT EXISTS first_name ON TABLE person TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS last_name ON TABLE person TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS title ON TABLE person TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS email ON TABLE person TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS person_aliases ON TABLE person TYPE Option<Array<Record<person_alias>>>;


// Defines text search indexes on various fields of the 'person' table.
DEFINE INDEX IF NOT EXISTS full_name_text_index ON TABLE person
    FIELDS full_name SEARCH ANALYZER name_analyzer BM25;
DEFINE INDEX IF NOT EXISTS first_name_text_index ON TABLE person
    FIELDS first_name SEARCH ANALYZER name_analyzer BM25;
DEFINE INDEX IF NOT EXISTS last_name_text_index ON TABLE person
    FIELDS last_name SEARCH ANALYZER name_analyzer BM25;
DEFINE INDEX IF NOT EXISTS title_text_index ON TABLE person
    FIELDS title SEARCH ANALYZER name_analyzer BM25;


DEFINE INDEX IF NOT EXISTS full_name_text_index ON TABLE person
    FIELDS full_name SEARCH ANALYZER name_analyzer BM25;
DEFINE INDEX IF NOT EXISTS first_name_text_index ON TABLE person
    FIELDS first_name SEARCH ANALYZER name_analyzer BM25;
DEFINE INDEX IF NOT EXISTS last_name_text_index ON TABLE person
    FIELDS last_name SEARCH ANALYZER name_analyzer BM25;
DEFINE INDEX IF NOT EXISTS title_text_index ON TABLE person
    FIELDS title SEARCH ANALYZER name_analyzer BM25;


DEFINE TABLE IF NOT EXISTS person_alias SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS full_name ON TABLE person_alias TYPE string;
DEFINE FIELD IF NOT EXISTS firm ON TABLE person_alias TYPE Record<firm>;
DEFINE FIELD IF NOT EXISTS person ON TABLE person_alias TYPE Record<person>;
DEFINE FIELD IF NOT EXISTS first_name ON TABLE person_alias TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS last_name ON TABLE person_alias TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS title ON TABLE person_alias TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS email ON TABLE person_alias TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS source_filing ON TABLE person_alias TYPE Option<Record<filing>>;


// Defines text search indexes on various fields of the 'person_alias' table.
DEFINE INDEX IF NOT EXISTS full_name_text_index ON TABLE person_alias
    FIELDS full_name SEARCH ANALYZER name_analyzer BM25;
DEFINE INDEX IF NOT EXISTS first_name_text_index ON TABLE person_alias
    FIELDS first_name SEARCH ANALYZER name_analyzer BM25;
DEFINE INDEX IF NOT EXISTS last_name_text_index ON TABLE person_alias
    FIELDS last_name SEARCH ANALYZER name_analyzer BM25;
DEFINE INDEX IF NOT EXISTS title_text_index ON TABLE person_alias
    FIELDS title SEARCH ANALYZER name_analyzer BM25;

// Defines a regular index on the 'email' field of the 'firm_alias' table.
DEFINE INDEX IF NOT EXISTS email ON TABLE person_alias
    FIELDS email;







