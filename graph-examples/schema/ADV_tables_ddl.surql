/*
This file defines the SurrealQL for this project.
*/

// Defines a custom analyzer named 'snowball_analyzer' for text searching.
// It uses the 'class' tokenizer (which tokenizes based on word boundaries)
// and applies two filters:
// 1. 'lowercase': Converts all tokens to lowercase for case-insensitive searching.
// 2. 'snowball(english)': Applies the Snowball stemming algorithm for English,
//    reducing words to their root form to improve search recall.
-- DEFINE ANALYZER IF NOT EXISTS snowball_analyzer
--     TOKENIZERS class
--     FILTERS lowercase, snowball(english);

// Defines another custom analyzer named 'name_analyzer' specifically for names.
// It uses the 'class' tokenizer and applies these filters:
// 1. 'lowercase': Converts tokens to lowercase.
// 2. 'ascii': Removes any non-ASCII characters.
// 3. 'ngram(2, 10)': Creates n-grams (sequences of characters) of length 2 to 10.
//    This is useful for partial name matching and handling typos.

DEFINE ANALYZER OVERWRITE name_analyzer TOKENIZERS
    class FILTERS lowercase, ascii, edgengram(2, 5);


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




DEFINE TABLE IF NOT EXISTS parent_firm SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS name ON TABLE parent_firm TYPE string;
DEFINE FIELD IF NOT EXISTS simple_name ON TABLE parent_firm TYPE string;
DEFINE FIELD IF NOT EXISTS firms ON TABLE parent_firm TYPE references<firm>;


DEFINE TABLE IF NOT EXISTS firm SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS name ON TABLE firm TYPE string;
DEFINE FIELD IF NOT EXISTS name_clean ON TABLE firm TYPE Option<string> DEFAULT fn::clean_company_string(name);
DEFINE FIELD IF NOT EXISTS name_embedding ON TABLE firm TYPE Option<array<float>> DEFAULT fn::firm_name_to_vector(name_clean);
DEFINE FIELD IF NOT EXISTS identifier ON TABLE firm TYPE string;
DEFINE FIELD IF NOT EXISTS firm_type ON TABLE firm TYPE Record<firm_type>;
DEFINE FIELD IF NOT EXISTS legal_name ON TABLE firm TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS city ON TABLE firm TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS state ON TABLE firm TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS country ON TABLE firm TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS postal_code ON TABLE firm TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS chief_compliance_officer ON TABLE firm TYPE Option<Record<person>>;
DEFINE FIELD IF NOT EXISTS parent_firm ON TABLE firm TYPE Option<Record<parent_firm>> REFERENCE;
//DEFINE FIELD IF NOT EXISTS firm_aliases ON TABLE firm TYPE Option<Array<Record<firm_alias>>>;


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





DEFINE TABLE IF NOT EXISTS firm_alias SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS firm ON TABLE firm_alias TYPE Record<firm> REFERENCE;
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
DEFINE FIELD IF NOT EXISTS source_filing ON TABLE firm_alias TYPE Option<Record<filing>> REFERENCE;
DEFINE FIELD IF NOT EXISTS pfid ON TABLE firm_alias TYPE Option<string>;



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
DEFINE FIELD IF NOT EXISTS source_filing ON TABLE custodian_for TYPE Record<filing> REFERENCE;
DEFINE FIELD IF NOT EXISTS custodian_type ON TABLE custodian_for TYPE Record<custodian_type>;
DEFINE FIELD IF NOT EXISTS custodian_as_listed ON TABLE custodian_for TYPE Option<object>;
DEFINE FIELD IF NOT EXISTS custodian_as_listed.legal_entity_identifier ON TABLE custodian_for TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS custodian_as_listed.sec_number ON TABLE custodian_for TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS custodian_as_listed.pfid ON TABLE custodian_for TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS custodian_as_listed.name ON TABLE custodian_for TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS custodian_as_listed.legal_name ON TABLE custodian_for TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS custodian_as_listed.country ON TABLE custodian_for TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS custodian_as_listed.state ON TABLE custodian_for TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS custodian_as_listed.city ON TABLE custodian_for TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS custodian_as_listed.postal_code ON TABLE custodian_for TYPE Option<string>;

DEFINE FIELD IF NOT EXISTS description ON TABLE custodian_for TYPE Option<string>;

DEFINE FIELD IF NOT EXISTS assets_under_management ON TABLE custodian_for TYPE Option<float>;
DEFINE FIELD IF NOT EXISTS related_person ON TABLE custodian_for TYPE Option<bool>;

DEFINE FIELD IF NOT EXISTS section_d_7b1 ON TABLE custodian_for TYPE Option<object>;

DEFINE FIELD IF NOT EXISTS section_d_7b1.percentage_owned_you_or_related ON TABLE custodian_for TYPE Option<float>;
DEFINE FIELD IF NOT EXISTS section_d_7b1.percentage_owned_funds ON TABLE custodian_for TYPE Option<float>;
DEFINE FIELD IF NOT EXISTS section_d_7b1.percentage_invested ON TABLE custodian_for TYPE Option<float>;
DEFINE FIELD IF NOT EXISTS section_d_7b1.unqualified_opinion ON TABLE custodian_for TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS section_d_7b1.fund_type_other ON TABLE custodian_for TYPE Option<string>;


// Defines a RELATION table named 'master_of_feeder' between two 'firm' records.
DEFINE TABLE IF NOT EXISTS master_of_feeder TYPE RELATION
IN firm OUT firm SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS source_filing ON TABLE master_of_feeder TYPE Record<filing> REFERENCE;
DEFINE FIELD IF NOT EXISTS master_fund_name ON TABLE master_of_feeder TYPE Option<string>;

           




DEFINE TABLE IF NOT EXISTS filing SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS filing_id ON TABLE filing TYPE int;
DEFINE FIELD IF NOT EXISTS firm ON TABLE filing TYPE Record<firm> REFERENCE;
DEFINE FIELD IF NOT EXISTS execution_type ON TABLE filing TYPE Record<ia_filing_execution_type>;
DEFINE FIELD IF NOT EXISTS signatory ON TABLE filing TYPE Record<person> REFERENCE;
DEFINE FIELD IF NOT EXISTS references ON TABLE filing TYPE references;

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
DEFINE FIELD IF NOT EXISTS first_name ON TABLE person TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS last_name ON TABLE person TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS title ON TABLE person TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS email ON TABLE person TYPE Option<string>;





DEFINE TABLE IF NOT EXISTS person_alias SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS full_name ON TABLE person_alias TYPE string;
DEFINE FIELD IF NOT EXISTS person ON TABLE person_alias TYPE Record<person> REFERENCE;
DEFINE FIELD IF NOT EXISTS first_name ON TABLE person_alias TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS last_name ON TABLE person_alias TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS title ON TABLE person_alias TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS email ON TABLE person_alias TYPE Option<string>;
DEFINE FIELD IF NOT EXISTS source_filing ON TABLE person_alias TYPE Option<Record<filing>> REFERENCE;



# this is a table to store a  word model in database
DEFINE TABLE IF NOT EXISTS firm_name_embedding_model TYPE NORMAL SCHEMAFULL;
DEFINE FIELD IF NOT EXISTS word ON firm_name_embedding_model TYPE string;
DEFINE FIELD IF NOT EXISTS embedding ON firm_name_embedding_model TYPE array<float>;




