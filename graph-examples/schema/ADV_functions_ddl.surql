
// Defines or overwrites a function to upsert (update or insert) a custodian type.
DEFINE FUNCTION OVERWRITE fn::custodian_type($custodian_type_name:string){
    // Upserts a record of type 'custodian_type' with the given name.
    // If a record with the same ID (derived from the name) exists, it's updated.
    // Otherwise, a new record is created.
    LET $custodian_type = (UPSERT type::thing("custodian_type",$custodian_type_name)
            CONTENT{"custodian_type": $custodian_type_name}).id[0];
    // Returns the ID of the upserted custodian type record.
    RETURN $custodian_type;
};



// Defines or overwrites a function to upsert a firm type.
DEFINE FUNCTION OVERWRITE fn::firm_type_upsert($firm_type_name:string){
    // Upserts a record of type 'firm_type' with the provided name.
    // If a record with the same ID (derived from the name) exists, it's updated.
    // Otherwise, a new record is created.
    LET $firm_type = (UPSERT type::thing("firm_type",$firm_type_name)
             CONTENT{"firm_type": $firm_type_name}).id[0];
    // Returns the ID of the upserted firm type record.
    RETURN $firm_type;
};

DEFINE FUNCTION OVERWRITE fn::string_match_score($match:option<string>,$value:option<string>){
    // Handles cases where both input strings are NONE, returning a neutral score of 0.5.

    IF $value IS NONE OR $match IS NONE THEN { RETURN 0; }
    ELSE {
         RETURN string::distance::normalized_damerau_levenshtein($match.lowercase(),$value.lowercase()); 
        
    }END;
};


// Defines or overwrites a function to upsert an IA filing execution type.
DEFINE FUNCTION OVERWRITE fn::execution_type_upsert($execution_type_name:string){
    // Upserts a record of type 'ia_filing_execution_type' with the given name.
    // If a record with the same ID (derived from the name) exists, it's updated.
    // Otherwise, a new record is created.
    LET $execution_type = (UPSERT type::thing("ia_filing_execution_type",$execution_type_name)
            CONTENT{"execution_type": $execution_type_name}).id[0];
    // Returns the ID of the upserted execution type record.
    RETURN $execution_type;
};





// Defines or overwrites a function to upsert a firm record.
DEFINE FUNCTION OVERWRITE fn::firm_upsert(
    $name: string,
    $firm_type_name: string,
    $legal_name: option<string>,
    $sec_number: option<string>,
    $pfid: option<string>,
    $legal_entity_identifier: option<string>,
    $cik: option<int>,
    $city: option<string>,
    $state: option<string>,
    $postal_code: option<string>,
    $country: option<string>,
    $section1: option<object>,
    $section_5d: option<object>,
    $section_5f: option<object>,
    $source_filing: option<Record<filing>>
    )
    {  
        // Determines the best identifier for the firm based on the provided optional identifiers.
        LET $identifier = fn::firm_best_identifier($legal_name, $sec_number, $pfid, $legal_entity_identifier,$cik);
        // Upserts the firm type using its name and retrieves its ID.
        LET $firm_type = fn::firm_type_upsert($firm_type_name);
        // Constructs the record ID for the firm.
        LET $firm = type::thing("firm", $identifier);

        // Upserts the chief compliance officer if the relevant data exists in $section1.
        LET $chief_compliance_officer =        
            IF $section1 IS NOT NONE AND $section1["chief_compliance_officer_name"]  IS NOT NONE THEN 
                fn::compliance_officer_upsert(
                        $firm,
                        $section1["chief_compliance_officer_name"],
                        $section1["latest_adv_filing_date"],
                        $section1["chief_compliance_officer_other_titles"],
                        $section1["chief_compliance_officer_e_mail"])
            ELSE
                NONE
            END;

        // Upserts the firm record, merging the provided data with any existing data.
        // Existing values are preserved if the new values are NONE.
        UPSERT $firm MERGE{
            name:IF name IS NONE THEN $name ELSE name END,
            name_clean:fn::clean_company_string($name),
            identifier:IF identifier IS NONE THEN $identifier ELSE identifier END,
            firm_type:IF firm_type IS NONE THEN $firm_type ELSE firm_type END,
            legal_name:IF legal_name IS NONE THEN $legal_name ELSE legal_name END,
            city:IF city IS NONE THEN $city ELSE city END,
            state:IF state IS NONE THEN $state ELSE state END,
            postal_code:IF postal_code IS NONE THEN $postal_code ELSE postal_code END,
            country:IF country IS NONE THEN $country ELSE country END,
            chief_compliance_officer:IF chief_compliance_officer IS NONE THEN $chief_compliance_officer ELSE chief_compliance_officer END,
            section1:IF section1 IS NONE THEN $section1 ELSE section1 END,
            section_5d:IF section_5d IS NONE THEN $section_5d ELSE section_5d END,
            section_5f:IF section_5f IS NONE THEN $section_5f ELSE section_5f END
        } RETURN NONE;

    
        // Upserts firm aliases based on various identifiers.
        LET $firm_aliases = fn::firm_aliases_upsert(
                    $firm,
                    $name,
                    $legal_name,
                    $firm_type_name,
                    $source_filing,
                    $sec_number,
                    $pfid,
                    $legal_entity_identifier,
                    $cik,
                    $city,
                    $state,
                    $postal_code,
                    $country);

        RETURN $firm;
    };




// Defines or overwrites a function to upsert a filing record.
DEFINE FUNCTION OVERWRITE fn::filing_upsert(
    $filing_id: int,
    $sec_number: string,
    $execution_type_name: string,
    $execution_date: datetime,
    $signatory_name: string,
    $signatory_title: string,
    $crc_number: option<string>)
    {
        // Upserts the execution type using its name and retrieves its ID.
        LET $execution_type = fn::execution_type_upsert($execution_type_name);

        // Determines the firm identifier based on the SEC number.
        LET $firm_identifier = fn::firm_best_identifier(NONE, $sec_number, NONE, NONE, NONE);
        // Constructs the record ID for the firm.
        LET $firm = type::thing("firm", $firm_identifier);
        // Constructs the record ID for the filing.
        LET $filing = type::thing("filing",$filing_id);

        // Upserts the signatory information.
        LET $signatory = fn::signatory_upsert(
            $filing,
            $signatory_name,
            $execution_date,
            $signatory_title
        ).id;


        // Creates a relation between the firm and the filing with the execution date.
        RELATE $firm->filed:[$firm,$filing]->$filing  CONTENT{
            in: $firm,
            out: $filing,
            execution_date: $execution_date
        } RETURN NONE;

        // Upserts the filing record, merging the provided data.
        UPSERT $filing MERGE{
            filing_id: $filing_id,
            firm: $firm,
            execution_type: $execution_type,
            signatory: $signatory,
            crc_number: $crc_number,
        } RETURN NONE;

        // Returns the record ID of the upserted filing.
        RETURN $filing;
    };






// Defines or overwrites a function to generate an array of potential firm identifiers.
DEFINE FUNCTION OVERWRITE fn::firm_identifier_array(
    $legal_name: Option<string>,
    $sec_number: Option<string>,
    $pfid: Option<string>,
    $legal_entity_identifier: Option<string>,
    $cik: Option<int>
)
{
    // Creates an array of potential identifiers, formatting each with a prefix.
    LET $identifiers =  [
        IF $sec_number IS NOT NONE THEN {
            "sec:" + $sec_number.lowercase();
        }END,
        IF $pfid IS NOT NONE THEN {
            "pfid:" + $pfid.lowercase();
        }END,
        IF $legal_entity_identifier IS NOT NONE THEN {
            "lei:" + $legal_entity_identifier.lowercase();
        }END,
        IF $cik IS NOT NONE THEN {
        "cik:" + <string>$cik;
        }END,
        IF $legal_name IS NOT NONE THEN {
            "ln:" + $legal_name.lowercase();
        }END
    ];
    // Filters out any NULL values from the array and returns the remaining identifiers.
    RETURN $identifiers.filter(|$v| $v IS NOT NONE);
};

// Defines or overwrites a function to determine the best single identifier for a firm based on priority.
DEFINE FUNCTION OVERWRITE fn::firm_best_identifier(
    $legal_name: Option<string>,
    $sec_number: Option<string>,
    $pfid: Option<string>,
    $legal_entity_identifier: Option<string>,
    $cik: Option<int>
) {
        // Prioritizes identifiers in the following order: SEC number, PFID, LEI, CIK, Legal Name.
        LET $identifier =
            IF $sec_number IS NOT NONE THEN
                "sec:" + $sec_number.lowercase()
            ELSE IF $pfid IS NOT NONE THEN
                "pfid:" + $pfid.lowercase()
            ELSE IF $legal_entity_identifier IS NOT NONE THEN
                "lei:" + $legal_entity_identifier.lowercase()
            ELSE IF $cik IS NOT NONE THEN
                "cik:" + <string>$cik
            ELSE
                "ln:" + $legal_name.lowercase()
            END;
            // Returns the highest priority non-null identifier.
            RETURN $identifier;
};




// Defines or overwrites a function to calculate a match score between two firm records based on various string fields.
DEFINE FUNCTION OVERWRITE fn::firm_match_score(
$legal_name_match:string,$legal_name:string,
$name_match:string,$name:string,
$name_clean_match:string,$name_clean:string,
$city_match:option<string>,$city:option<string>,
$state_match:option<string>,$state:option<string>,
$country_match:option<string>,$country:option<string>,
$min_score:option<float>)

{
    // Calculates individual string match scores for legal name, name, city, state, and country.
    LET $legal_name_score = fn::string_match_score($legal_name_match,$legal_name);
    LET $name_score = fn::string_match_score($name_match,$name);
    LET $name_clean_score = fn::string_match_score($name_clean_match,$name_clean);

    
    LET $city_score = fn::string_match_score($city_match,$city);
    LET $state_score = fn::string_match_score($state_match,$state);
    LET $country_score = fn::string_match_score($country_match,$country);
    
    // Sets a threshold; if both legal name and name scores are below this, it's considered no match.
    LET $similarity_threshold = 0.1; #1 is identical
    
    #IF $legal_name_score<$similarity_threshold AND $name_score<$similarity_threshold THEN { RETURN NONE } END;
    
    LET $name_score = math::mean([$name_score,$legal_name_score,$name_clean_score]);

    // Assigns a lower weight to the geographic match scores.
    # LET $geo_factor = 2.0; #the higher the less weight to geo matching
    // Combines the base firm score with the weighted geographic scores to produce the final match score.
     

    
    LET $country_weight = IF $country_match THEN 0.05 ELSE 0 END;
    LET $state_weight = IF $state_match THEN 0.05 ELSE 0 END;
    LET $city_weight = IF $city_match THEN 0.05 ELSE 0 END;
    
    LET $name_weight = 1 - $country_weight  - $state_weight - $city_weight;
    
    LET $final_score = $name_weight * $name_score 
                        + $country_weight * $country_score 
                        + $state_weight * $state_score
                        + $city_weight * $city_score;


    LET $min_score = $min_score ?? 0.5;

    RETURN IF $final_score > $min_score THEN $final_score ELSE NONE END;
};
 


// Defines or overwrites a function to find a matching firm based on name and optional geographic details.

DEFINE FUNCTION OVERWRITE fn::find_match_for_firm(
    $name: string,
    $legal_name: string,
    $city: Option<string>,
    $state: Option<string>,
    $country: Option<string>){

    // Queries for firms where either the legal name or name loosely matches the input,
    // calculates a match score for each, and orders the results by score in descending order.
    
    LET $name_clean = fn::clean_company_string($name);
    LET $name_clean_vector = fn::firm_name_to_vector($name_clean);
    

    
    LET $matched_firms = 
        IF $name_clean_vector[0] != MATH::NEG_INF THEN 
                SELECT * FROM
                (
                    SELECT id,name,section_5f.total_regulatory_assets AS assets, fn::firm_match_score(
                            $legal_name,legal_name,
                            $name,name,
                            $name_clean,name_clean,
                            $city,city,
                            $state,state,
                            $country,country
                        ) AS _score FROM firm WHERE
                                     name_embedding <|10,50|> $name_clean_vector )
                    WHERE _score IS NOT NONE ORDER BY _score DESC, assets DESC

        ELSE 
            SELECT * FROM
            (
                SELECT id,name,section_5f.total_regulatory_assets AS assets, fn::firm_match_score(
                        $legal_name,legal_name,
                        $name,name,
                        $name_clean,name_clean,
                        $city,city,
                        $state,state,
                        $country,country
                    ) AS _score FROM firm WHERE
                                 name_clean.starts_with($name_clean) )
                WHERE _score IS NOT NONE ORDER BY _score DESC, assets DESC

        END;
    
    // If any matches are found, return the ID of the top-scoring firm; otherwise, return NONE.
    RETURN IF array::len($matched_firms) > 0 THEN $matched_firms.id[0] ELSE NONE END;
    

};

// Defines or overwrites a function to find a matching firm based on firm aliases.
DEFINE FUNCTION OVERWRITE fn::find_alias_match_for_firm(
    $legal_name: string, // The legal name of the firm to search for.
    $sec_number: Option<string>, // The SEC number of the firm, if available.
    $pfid: Option<string>, // The PFID of the firm, if available.
    $legal_entity_identifier: Option<string>, // The LEI of the firm, if available.
    $cik: Option<int> // The CIK of the firm, if available.
) {

    // If an SEC number is provided, search for a firm alias using the SEC number.
    IF $sec_number IS NOT NONE THEN {
        // Construct the record ID for the firm alias using the "sec:" prefix.
        LET $firm_alias = type::thing("firm_alias", "sec:" + $sec_number);
        // If a firm alias with this ID exists and has a linked firm, return that firm.
        IF $firm_alias["firm"] IS NOT NONE THEN {
            RETURN $firm_alias["firm"];
        } END;
    } END;

    // If a PFID is provided, search for a firm alias using the PFID.
    IF $pfid IS NOT NONE THEN {
        // Construct the record ID for the firm alias using the "pfid:" prefix.
        LET $firm_alias = type::thing("firm_alias", "pfid:" + $pfid);
        // If a firm alias with this ID exists and has a linked firm, return that firm.
        IF $firm_alias["firm"] IS NOT NONE THEN {
            RETURN $firm_alias["firm"];
        } END;
    } END;

    // If a Legal Entity Identifier (LEI) is provided, search for a firm alias using the LEI.
    IF $legal_entity_identifier IS NOT NONE THEN {
        // Construct the record ID for the firm alias using the "lei:" prefix.
        LET $firm_alias = type::thing("firm_alias", "lei:" + $legal_entity_identifier);
        // If a firm alias with this ID exists and has a linked firm, return that firm.
        IF $firm_alias["firm"] IS NOT NONE THEN {
            RETURN $firm_alias["firm"];
        } END;
    } END;

    // If a CIK is provided, search for a firm alias using the CIK.
    IF $cik IS NOT NONE THEN {
        // Construct the record ID for the firm alias using the "cik:" prefix.
        LET $firm_alias = type::thing("firm_alias", "cik:" + <string>$cik);
        // If a firm alias with this ID exists and has a linked firm, return that firm.
        IF $firm_alias["firm"] IS NOT NONE THEN {
            RETURN $firm_alias["firm"];
        } END;
    } END;

    // If none of the above identifiers matched, search for a firm alias using the legal name.
    // This is the last resort, as legal names might not be unique.
    LET $firm_alias = type::thing("firm_alias", "ln:" + $legal_name);
    // If a firm alias with this ID exists and has a linked firm, return that firm.
    IF $firm_alias["firm"] IS NOT NONE THEN {
        RETURN $firm_alias["firm"];
    } ELSE {
        // If no matching firm alias is found with any of the provided identifiers, return NONE.
        RETURN NONE;
    } END;

};

// Defines or overwrites a function to upsert firm alias records.
// These aliases provide alternative identifiers and names for a firm.
DEFINE FUNCTION OVERWRITE fn::firm_aliases_upsert(
    $firm: Record<firm>, // The primary firm record to which the aliases will be linked.
    $name: string, // The current primary name of the firm.
    $legal_name: string, // The current legal name of the firm.
    $firm_type_name: string, // The type of the firm.
    $source_filing : Option<Record<filing>>, // The filing record that provided this alias information.
    $sec_number: Option<string>, // The SEC number of the firm, if available.
    $pfid: Option<string>, // The private fund identifier, if available.
    $legal_entity_identifier: Option<string>, // The legal entity identifier, if available.
    $cik: Option<int>, // The Central Index Key, if available.
    $city: Option<string>, // The city of the firm's primary location.
    $state: Option<string>, // The state of the firm's primary location.
    $postal_code: Option<string>, // The postal code of the firm's primary location.
    $country: Option<string> // The country of the firm's primary location.
    ){

        // Generates an array of potential identifiers for the firm.
        LET $identifiers =
            fn::firm_identifier_array($legal_name, $sec_number, $pfid, $legal_entity_identifier,$cik);
        // Upserts the firm type.
        LET $firm_type = fn::firm_type_upsert($firm_type_name);

        // Iterates through each generated identifier to upsert a firm alias record.
        FOR $identifier IN $identifiers{

            // Constructs the record ID for the firm alias.
            LET $firm_alias = type::thing("firm_alias",$identifier);
            // Upserts the firm alias record, merging new information with existing data.
            UPSERT $firm_alias MERGE{
                source_filing:IF source_filing IS NONE THEN $source_filing ELSE source_filing END,
                firm:IF firm IS NONE THEN $firm ELSE firm END,
                name:IF name IS NONE THEN $name ELSE name END,
                legal_name:IF legal_name IS NONE THEN $legal_name ELSE legal_name END,
                firm_type:IF firm_type IS NONE THEN $firm_type ELSE firm_type END,
                sec_number:IF sec_number IS NONE THEN $sec_number ELSE sec_number END,
                legal_entity_identifier:IF legal_entity_identifier IS NONE THEN $legal_entity_identifier ELSE legal_entity_identifier END,
                cik:IF cik IS NONE THEN $cik ELSE cik END,
                pfid:IF pfid IS NONE THEN $pfid ELSE pfid END,
                city:IF city IS NONE THEN $city ELSE city END,
                state:IF state IS NONE THEN $state ELSE state END,
                postal_code:IF postal_code IS NONE THEN $postal_code ELSE postal_code END,
                country:IF country IS NONE THEN $country ELSE country END
            } RETURN NONE;

            -- // Updates the primary firm record by adding the newly created/updated alias to its list of aliases.
            -- UPDATE $firm
            --     SET
            --     firm_aliases = IF $firm["firm_aliases"] IS  NONE THEN [$firm_alias] ELSE firm_aliases.union([$firm_alias]) END
            --     RETURN NONE;
        };

        // Returns an array of the newly created/updated firm alias record IDs.
        RETURN $identifiers.map(|$v| type::thing("firm_alias",$v));
    };



// Defines or overwrites a function to either retrieve an existing firm or create a new one.
DEFINE FUNCTION OVERWRITE fn::firm_get_or_upsert(
    $source_filing : Record<filing>, // The filing record associated with this firm information.
    $name: string, // The primary name of the firm.
    $legal_name: string, // The legal name of the firm.
    $firm_type_name_if_insert: string, // The firm type to use if a new firm needs to be inserted.
    $sec_number: Option<string>, // The SEC number of the firm, if available.
    $pfid: Option<string>, // The private fund identifier, if available.
    $legal_entity_identifier: Option<string>, // The legal entity identifier, if available.
    $cik: Option<int>, // The Central Index Key, if available.
    $city: Option<string>, // The city of the firm's primary location.
    $state: Option<string>, // The state of the firm's primary location.
    $postal_code: Option<string>, // The postal code of the firm's primary location.
    $country: Option<string> // The country of the firm's primary location.

    ){

    // Attempts to find an existing firm by matching against its aliases.
    LET $firm = fn::find_alias_match_for_firm(
            $legal_name,
            $sec_number,
            $pfid,
            $legal_entity_identifier,
            $cik
        );

    // If a firm is found via its alias, return that firm.
    IF $firm IS NOT NONE THEN{
        RETURN $firm;
    } ELSE {
        // If no firm is found via alias, search for similar firms based on name and location.
        LET $firm =
            fn::find_match_for_firm  (
                $name,
                $legal_name,
                $city,
                $state,
                $country
            );

        // If a similar firm is found...
        IF $firm IS NOT NONE THEN{
            // Upsert new alias information for the found firm.
            LET $firm_aliases = fn::firm_aliases_upsert(
                $firm,
                $name,
                $legal_name,
                $firm_type_name_if_insert,
                $source_filing,
                $sec_number,
                $pfid,
                $legal_entity_identifier,
                $cik,
                $city,
                $state,
                $postal_code,
                $country);

            // Return the found firm.
            RETURN $firm;
        } ELSE {
            // If no existing or similar firm is found, upsert a new firm.
            LET $section1 = IF $sec_number IS NOT NONE THEN {"sec_number":$sec_number} ELSE  NONE END;

            LET $firm = fn::firm_upsert(
                                $name,$firm_type_name_if_insert,$name,$sec_number,$pfid,$legal_entity_identifier,$cik,$city,$state,$postal_code,$country, $section1, NONE, NONE,$source_filing
                            ).id;
            // Return the ID of the newly created firm.
            RETURN $firm;
        }
        END;
    } END;
};



// Defines or overwrites a function to retrieve or create a "RAUM Custodian" firm.
DEFINE FUNCTION OVERWRITE fn::raum_custodian_get_or_upsert(
    $source_filing : Record<filing>, // The filing record associated with this custodian information.
    $name: string, // The name of the RAUM custodian.
    $legal_name: string, // The legal name of the RAUM custodian.
    $sec_number: Option<string>, // The SEC number of the RAUM custodian, if available.
    $legal_entity_identifier: Option<string>, // The LEI of the RAUM custodian, if available.
    $city: Option<string>, // The city of the RAUM custodian's location.
    $state: Option<string>, // The state of the RAUM custodian's location.
    $country: Option<string> // The country of the RAUM custodian's location.
    ){
        // Calls the generic firm get or upsert function with the specific "RAUM Custodian" type.
        RETURN fn::firm_get_or_upsert(
            $source_filing,
            $name,
            $legal_name,
            "RAUM Custodian",
            $sec_number,
            NONE,
            $legal_entity_identifier,
            NONE,
            $city,
            $state,
            NONE,
            $country
        );

    };


// Defines or overwrites a function to upsert a Reporting Agent Under Management (RAUM) relationship.
DEFINE FUNCTION OVERWRITE fn::raum_upsert(
    $filing_id: int, // The ID of the filing record.
    $primary_business_name: string, // The primary business name of the RAUM.
    $legal_name: string, // The legal name of the RAUM.
    $sec_number: Option<string>, // The SEC number of the RAUM, if available.
    $legal_entity_identifier: Option<string>, // The LEI of the RAUM, if available.
    $city: Option<string>, // The city of the RAUM's location.
    $state: Option<string>, // The state of the RAUM's location.
    $country: Option<string>, // The country of the RAUM's location.
    $is_related_person: Option<string>, // Indicates if the RAUM is a related person.
    $assets_under_management: Option<float> // The assets under management by the RAUM, if available.
    )
    {
        // Retrieves the filing record.
        LET $filing = type::thing("filing",$filing_id);
        // Retrieves the firm associated with the filing.
        LET $filing_firm = $filing["firm"];
        IF $filing_firm IS NONE THEN {
            # invalid filing!
            RETURN NONE;
        } END;
        // Retrieves or creates the custodian firm for the RAUM.
        LET $custodian_firm = fn::raum_custodian_get_or_upsert(
            $filing,
            $primary_business_name,
            $legal_name,
            $sec_number,
            $legal_entity_identifier,
            $city,
            $state,
            $country);

        // Determines if the RAUM is a related person (converts string options to boolean).
        LET $related_person = IF $is_related_person IS NONE THEN FALSE ELSE $is_related_person.lowercase() in ["yes","true","1","y"] END;





        // Creates a relationship indicating the custodian for the filing firm is the RAUM custodian.
        RELATE $custodian_firm->custodian_for:[$custodian_firm,$filing_firm]->$filing_firm  CONTENT{
            in: $custodian_firm,
            out: $filing_firm,
            source_filing: $filing,
            custodian_type: custodian_type:`RAUM`,
            legal_entity_identifier: $legal_entity_identifier,
            assets_under_management: $assets_under_management,
            related_person: $related_person,
            custodian_as_listed:{
                legal_entity_identifier: $legal_entity_identifier,
                sec_number: $sec_number,
                name: $primary_business_name,
                legal_name: $legal_name,
                country: $country,
                state: $state,
                city: $city,
            }
        } RETURN NONE;
    };



// Defines or overwrites a function to retrieve or create a Private Fund (PF) custodian firm.
DEFINE FUNCTION OVERWRITE fn::pf_custodian_get_or_upsert(
    $source_filing : Record<filing>, // The filing record associated with this custodian information.
    $name: string, // The name of the private fund.
    $fund_id: string, // The identifier of the private fund.
    $fund_type: string, // The type of the private fund.
    $is_feeder_fund: Option<string>, // Indicates if the fund is a feeder fund.
    $master_fund_id: Option<string>, // The identifier of the master fund, if it's a feeder fund.
    $master_fund_name: Option<string>, // The name of the master fund, if it's a feeder fund.
    $state: Option<string>, // The state of the fund's location.
    $country: Option<string> // The country of the fund's location.
    ){

        // Retrieves or creates the firm record for the private fund custodian.
        LET $pf_firm = fn::firm_get_or_upsert(
            $source_filing,
            $name,
            $name,
            $fund_type,
            NONE,
            $fund_id,
            NONE,
            NONE,
            NONE,
            $state,
            NONE,
            $country
        );

        // Determines if the fund is a feeder fund (converts string options to boolean).
        LET $feeder_fund = IF $is_feeder_fund IS NONE THEN FALSE ELSE $is_feeder_fund.lowercase() in ["yes","true","1","y"] END;

        // If the fund is a feeder fund and has a master fund ID...
        IF $feeder_fund = True AND $master_fund_id IS NOT NONE THEN {
            // Construct the record ID for the master fund.
            LET $master_firm = type::thing("firm",fn::firm_best_identifier(NONE, NONE, $master_fund_id, NONE,NONE));
            // Creates a relationship indicating this fund is a feeder fund of the master fund.
            RELATE $master_firm->master_of_feeder:[$master_firm,$pf_firm]->$pf_firm  CONTENT{
                in: $master_firm,
                out: $pf_firm,
                source_filing: $source_filing,
                master_fund_name: $master_fund_name
            } RETURN NONE;

        } END;

        // Returns the firm record of the private fund custodian.
        RETURN $pf_firm;

    };


// Defines or overwrites a function to upsert a Private Fund (PF) relationship.
DEFINE FUNCTION OVERWRITE fn::pf_upsert(
    $filing_id: int, // The ID of the filing record.

    $name: string, // The name of the private fund.
    $fund_id: string, // The identifier of the private fund.
    $fund_type: string, // The type of the private fund.
    $is_feeder_fund: Option<string>, // Indicates if the fund is a feeder fund.
    $gross_asset_value: Option<float>, // The gross asset value of the fund, if available.
    $percentage_owned_you_or_related: Option<float>, // The percentage owned by you or related parties, if available.
    $percentage_owned_funds: Option<float>, // The percentage owned by other funds, if available.
    $percentage_invested: Option<float>, // The percentage invested in the fund, if available.
    $unqualified_opinion: Option<string>, // Indicates if the fund received an unqualified opinion.

    $master_fund_id: Option<string>, // The identifier of the master fund, if it's a feeder fund.
    $master_fund_name: Option<string>, // The name of the master fund, if it's a feeder fund.
    $state: Option<string>, // The state of the fund's location.
    $country: Option<string>, // The country of the fund's location.
    $fund_type_other: Option<string> // Other description of the fund type, if applicable.

)
    {
        // Retrieves the filing record.
        LET $filing = type::thing("filing",$filing_id);
        // Retrieves the firm associated with the filing.
        LET $filing_firm = $filing["firm"];
        IF $filing_firm IS NONE THEN {
            # invalid filing!
            RETURN NONE;
        } END;

        // Retrieves or creates the custodian firm for the private fund.
        LET $custodian_firm = fn::pf_custodian_get_or_upsert(
            $filing,
            $name,
            $fund_id,
            $fund_type,
            $is_feeder_fund,
            $master_fund_id,
            $master_fund_name,
            $state,
            $country);


        // Creates a relationship indicating the custodian for the filing firm is the private fund custodian.
        RELATE $custodian_firm->custodian_for:[$custodian_firm,$filing_firm]->$filing_firm  CONTENT{
            in: $custodian_firm,
            out: $filing_firm,
            source_filing: $filing,
            custodian_type: custodian_type:`PF`,
            assets_under_management: $gross_asset_value,
            section_d_7b1: {
                percentage_owned_you_or_related: $percentage_owned_you_or_related,
                percentage_owned_funds: $percentage_owned_funds,
                percentage_invested: $percentage_invested,
                unqualified_opinion: $unqualified_opinion,
                fund_type_other: $fund_type_other
            },
            custodian_as_listed:{
                legal_entity_identifier: NONE,
                sec_number: NONE,
                pfid: $fund_id,
                name: $name,
                legal_name: $name,
                country: $country,
                state: $state,
                city: $city
            }
        } RETURN NONE;
    };

// Defines or overwrites a function to retrieve or create a "Books and Records" (B&R) custodian firm.
DEFINE FUNCTION OVERWRITE fn::b_and_r_custodian_get_or_upsert(
    $source_filing : Record<filing>, // The filing record associated with this custodian information.
    $name: string, // The name of the B&R custodian.
    $city: Option<string>, // The city of the B&R custodian's location.
    $state: Option<string>, // The state of the B&R custodian's location.
    $postal_code: Option<string>, // The postal code of the B&R custodian's location.
    $country: Option<string> // The country of the B&R custodian's location.
    ){
        // Calls the generic firm get or upsert function with the specific "Records Custodian" type.
        RETURN fn::firm_get_or_upsert(
            $source_filing,
            $name,
            $name,
            "Records Custodian",
            NONE,
            NONE,
            NONE,
            NONE,
            $city,
            $state,
            $postal_code,
            $country
        );

    };


// Defines or overwrites a function to upsert a "Books and Records" (B&R) relationship.
DEFINE FUNCTION OVERWRITE fn::b_and_r_upsert(
    $filing_id: int, // The ID of the filing record.
    $name: string, // The name of the books and records custodian.
    $type: string, // The type of the books and records being custodied.
    $city: Option<string>, // The city of the custodian's location.
    $state: Option<string>, // The state of the custodian's location.
    $postal_code: Option<string>, // The postal code of the custodian's location.
    $country: Option<string>, // The country of the custodian's location.
    $description: Option<string> // A description of the books and records being custodied.
    )
    {

        // Retrieves the filing record.
        LET $filing = type::thing("filing",$filing_id);

        // Retrieves the firm associated with the filing.
        LET $filing_firm = $filing["firm"];
        IF $filing_firm IS NONE THEN {
            # invalid filing!
            RETURN NONE;
        } END;
        // If there's no firm associated with the filing, return NONE.
        IF $filing_firm IS NONE THEN {
            # no filing!
            RETURN NONE;
        }END;

        // Retrieves or creates the custodian type based on the provided string.
        LET $custodian_type = fn::custodian_type($type);

        // Retrieves or creates the firm record for the books and records custodian.
        LET $custodian_firm = fn::b_and_r_custodian_get_or_upsert(
            $filing,
            $name,
            $city,
            $state,
            $postal_code,
            $country);


        // Creates a relationship indicating the custodian for the filing firm is the B&R custodian.
        RELATE $custodian_firm->custodian_for:[$custodian_firm,$filing_firm]->$filing_firm  CONTENT{
            in: $custodian_firm,
            out: $filing_firm,
            source_filing: $filing,
            custodian_type: $custodian_type,
            description: $description,
            custodian_as_listed:{
                legal_entity_identifier: NONE,
                sec_number: NONE,
                pfid: NONE,
                name: $name,
                legal_name: $name,
                country: $country,
                state: $state,
                city: $city,
                postal_code: $postal_code
            }
        } RETURN NONE;
    };


// Defines or overwrites a function to extract first and last name parts from a full name string.
DEFINE FUNCTION OVERWRITE fn::get_name_parts_from_full_name(
    $full_name: string)
    {
        // If the full name is NONE, return an object with both first and last names as NONE.
        IF $full_name IS NONE THEN {
            RETURN {
                first_name: NONE,
                last_name: NONE
            };
        } END;

        // Split the full name string by spaces.
        LET $name_parts = $full_name.split(" ");
        // If there's only one part, assume it's the last name.
        IF array::len($name_parts) = 1 THEN {
            RETURN {
                first_name: NONE,
                last_name: $name_parts[0]
            };
        } END;
        // The last part is the last name.
        LET $last_name = $name_parts[array::len($name_parts)-1];
        // All parts before the last one constitute the first name.
        LET $first_name = array::slice($name_parts,0,array::len($name_parts)-1).join(' ');
        // Return an object containing the extracted first and last names.
        RETURN {
            first_name: $first_name,
            last_name: $last_name
        };
    };

// Defines or overwrites a function to generate an array of potential firm identifiers.
DEFINE FUNCTION OVERWRITE fn::person_identifier_array(
    $full_name: Option<string>,
    $email: Option<string>,
)
{
    // Creates an array of potential identifiers, formatting each with a prefix.
    LET $identifiers =  [
        IF $full_name IS NOT NONE THEN {
            "fn:" + $full_name.lowercase();
        }END,
        IF $email IS NOT NONE THEN {
            "e:" + $email.lowercase();
        }END
    ];
    // Filters out any NULL values from the array and returns the remaining identifiers.
    RETURN $identifiers.filter(|$v| $v IS NOT NONE);
};


// Defines or overwrites a function to find a matching person alias for a given firm, full name, and optional email.
DEFINE FUNCTION OVERWRITE fn::find_alias_match_for_person(
    $full_name: string, // The full name of the person.
    $email: Option<string> // The email address of the person, if available.
    ){
    // If an email is provided, try to find a person alias based on the firm and email.
    IF $email IS NOT NONE THEN {
        // Construct the record ID for the person alias using the firm and a prefixed email.
        LET $person_alias = type::thing("person_alias","e:" +$email.lowercase());
        // If a person alias with this ID exists and has a linked person, return that person.
        IF $person_alias["person"] IS NOT NONE THEN {
            RETURN $person_alias["person"];
        } END;
    } END;

    // If no match is found via email (or no email was provided), try to find a person alias
    // based on the firm and the full name.
    LET $person_alias = type::thing("person_alias","fn:" +$full_name.lowercase());
    // If a person alias with this ID exists and has a linked person, return that person.
    IF $person_alias["person"] IS NOT NONE THEN {
        RETURN $person_alias["person"];
    } ELSE { RETURN NONE; } END;

    };



// Defines or overwrites a function to calculate a match score between two person records based on various fields.
DEFINE FUNCTION OVERWRITE fn::person_match_score(
$full_name_match:string,$full_name:string,
$last_name_match:option<string>,$last_name: option<string>,
$first_name_match:option<string>,$first_name: option<string>,
$title_match:option<string>,$title:option<string>){
    // Calculate individual string match scores for full name, last name, first name, and title.
    LET $full_name_score = fn::string_match_score($full_name_match,$full_name);
    LET $last_name_score = fn::string_match_score($last_name_match,$last_name);
    LET $first_name_score = fn::string_match_score($first_name_match,$first_name);
    LET $title_score = fn::string_match_score($title_match,$title);

    // Define weights for each field in the overall match score.
    LET $full_name_weight = 1.0;
    LET $last_name_weight = 0.5;
    LET $first_name_weight = 0.5;
    LET $title_weight = 0.5;
    // Calculate the weighted average of the individual scores to get the final match score.
    LET $ft_score = $full_name_weight * $full_name_score +
           $last_name_weight * $last_name_score +
           $first_name_weight * $first_name_score +
           $title_weight * $title_score;

    RETURN $ft_score;
};


// Defines or overwrites a function to find a matching person for a given firm based on name and optional title.
DEFINE FUNCTION OVERWRITE fn::find_match_for_person(
    $full_name: string, // The full name of the person to match.
    $first_name: Option<string>, // The first name of the person to match.
    $last_name: Option<string>, // The last name of the person to match.
    $title: Option<string> // The title of the person to match.
    ){

    // Query for people associated with the given firm, calculate a match score,
    // and order the results by score in descending order.
    LET $matched_people = SELECT id, fn::person_match_score(
            $full_name,full_name,
            $last_name,last_name,
            $first_name,first_name,
            $title,title
        ) AS _score FROM person WHERE 
                    full_name @1@ $full_name OR (full_name @2@ $last_name AND full_name @3@ $first_name) ORDER BY _score DESC;
    // Return the ID of the top-scoring person, if any.
    RETURN $matched_people.id[0];
};


// Defines or overwrites a function to either retrieve an existing person or create a new one.
DEFINE FUNCTION OVERWRITE fn::get_person_or_upsert(
    $full_name: string, // The full name of the person.
    $filing:Option<Record<filing>>, // The filing record associated with this person information.
    $first_name: Option<string>, // The first name of the person.
    $last_name: Option<string>, // The last name of the person.
    $title: Option<string>, // The title of the person.
    $email: Option<string> // The email address of the person.
    ){

    // Attempt to find an existing person by matching against their aliases.
    LET $person = fn::find_alias_match_for_person(
            $full_name,
            NONE // Initially search without email for broader matching.
        );

    // If a person is found via alias, return that person.
    IF $person IS NOT NONE THEN{
        RETURN $person;
    } ELSE {
        // If no person is found via alias, try to find a match based on name.
        LET $name_parts = fn::get_name_parts_from_full_name($full_name);
        LET $person_match_id = fn::find_match_for_person(
            $full_name,
            $name_parts["first_name"],
            $name_parts["last_name"],
            $title
        );

        IF $person_match_id IS NOT NONE THEN{
            LET $person = type::thing("person",$person_match_id);
            // If a match is found, upsert a new alias for this person with the provided details.
            LET $person_alias = fn::person_aliases_upsert(
                $person,
                $full_name,
                $filing,
                $first_name,
                $last_name,
                $title,
                $email);
            RETURN $person;
        } ELSE {
            // If no match is found, upsert a new person record.
            LET $person = fn::person_upsert(
                $full_name,
                $first_name,
                $last_name,
                $title,
                $email
            );

            // Also, create a new alias for this newly created person.
            LET $person_alias = fn::person_aliases_upsert(
                $person,
                $full_name,
                $filing,
                $first_name,
                $last_name,
                $title,
                $email);
            RETURN $person;

        }END;
    }END;
};

// Defines or overwrites a function to upsert a person alias record.
// These aliases provide alternative names and contact information for a person within a specific firm.
DEFINE FUNCTION OVERWRITE fn::person_aliases_upsert(
    $person: Record<person>, // The primary person record to which this alias belongs.
    $full_name: string, // The full name of the person alias.
    $source_filing : Option<Record<filing>>, // The filing record that provided this alias information.
    $first_name: Option<string>, // The first name of the person alias.
    $last_name: Option<string>, // The last name of the person alias.
    $title: Option<string>, // The title of the person alias.
    $email: Option<string> // The email address of the person alias.
    )
    {
        // Determine the identifier for the person alias based on email or full name.

        LET $identifiers =
            fn::person_identifier_array($full_name, $email);
        // Upserts the firm type.

        // Iterates through each generated identifier to upsert a firm alias record.
        FOR $identifier IN $identifiers{


            // Upsert the person alias record, merging new information with existing data.
            LET $person_alias = type::thing("person_alias",$identifier);
            UPSERT $person_alias MERGE{
                source_filing: $source_filing,
                person: $person,
                full_name: $full_name,
                first_name: $first_name,
                last_name: $last_name,
                title: $title,
                email: $email
            } RETURN NONE;
        };
        

        // Update the primary person record by adding the newly created/updated alias to its list of aliases.
        -- UPDATE $person
        --     SET
        --     person_aliases = IF $person["person_aliases"] IS  NONE THEN [$person_alias] ELSE person_aliases.union([$person_alias]) END
        --     RETURN NONE;

        // Return the record ID of the upserted person (using full name and firm as a unique key).
        RETURN  type::thing("person",$full_name);
    };


// Defines or overwrites a function to upsert a person record.
DEFINE FUNCTION OVERWRITE fn::person_upsert(
    $full_name: string, // The full name of the person.
    $first_name: Option<string>, // The first name of the person.
    $last_name: Option<string>, // The last name of the person.
    $title: Option<string>, // The title of the person.
    $email: Option<string> // The email address of the person.
    )
    {
        // Upsert the person record, using full name and firm as a unique key, and merge the provided data.
        LET $person = type::thing("person",$full_name);
        UPSERT $person MERGE{
            full_name: $full_name,
            first_name: $first_name,
            last_name: $last_name,
            title: $title,
            email: $email
        };
        // Return the record ID of the upserted person.
        RETURN  $person;
    };




// Defines or overwrites a function to upsert a signatory (a person who signed a filing) record and create a relationship.
DEFINE FUNCTION OVERWRITE fn::signatory_upsert(
$filing:Record<filing>, // The filing the person signed.
$full_name:string, // The full name of the signatory.
$execution_date:datetime, // The date the filing was executed.
$title:Option<string> // The title of the signatory at the time of signing.
)
{
    LET $full_name = fn::clean_name_string($full_name);
    // Extract first and last names from the full name.
    LET $name_parts = fn::get_name_parts_from_full_name($full_name);
    // Get or upsert the person record for the signatory.
    LET $signatory = fn::get_person_or_upsert(
                $full_name,
                $filing,
                $name_parts["first_name"],
                $name_parts["last_name"],
                $title,
                NONE // Signatories typically don't have an email in this context.
            ).id;

    // Create a relationship indicating that the person signed the filing.
    RELATE $signatory->signed:[$signatory,$filing]->$filing  CONTENT{
        in: $signatory,
        out: $filing,
        execution_date: $execution_date,
        signatory_title: $title
    } RETURN NONE;

    // Return the ID of the signatory person record.
    RETURN $signatory;
};

DEFINE FUNCTION OVERWRITE fn::clean_name_string($name: string){
    LET $name = IF $name IS NONE THEN NONE ELSE 
        $name.lowercase()
        .replace("/s/","")
        .replace("/ss/","")
        .replace("/","")
        .replace("jr","")
        .replace("ii","")
        .replace("iii","")
        .replace("  "," ")
        .replace(".","").trim()
    END;
    LET $name_arr = $name.split(",");
    LET $name_arr_len = $name_arr.len();
    IF $name_arr_len > 0 THEN {
        // If the name contains a comma, split it and return the second part (after the comma).
        LET $last_name = $name_arr[0].trim();
        LET $rest_of_name = $name_arr.slice(1,$name_arr_len).join(" ").trim();
        RETURN ($rest_of_name + " " + $last_name).trim();
    } END;
    RETURN $name;
};


DEFINE FUNCTION OVERWRITE fn::clean_company_string($name: string){
    IF $name IS NONE THEN RETURN NONE; END;

    LET $geo_words = [
    "AMERICAN",
    "AMERICAS",
    "ASIA",
    "ASIAPACIFIC",
    "BOSTON",
    "EUROPE",
    "GLOBAL",
    "INTERNATIONAL",
    "IRELAND",
    "LONDON",
    "LUXEMBOURG",
    "PACIFIC",
    "UK",
    "US",
    "USA",
    "WORLD"
    ];

    
    LET $jargon_words = [
    "ADVISER",
    "ADVISERS",
    "ADVISOR",
    "ADVISORS",
    "ADVOCATE",
    "ADVOCATES",
    "ADVISORY",
    "ALTERNATIVE",
    "ASSET",
    "ASSETS",
    "ASSOCIATES",
    "CAPITAL",
    "CENTER",
    "CLIENT",
    "CO",
    "COMPANY",
    "CONSULTING",
    "CORNERSTONE",
    "CORPORATION",
    "COUNSEL",
    "CREDIT",
    "DIVERSIFIED",
    "EQUITIES",
    "EQUITY",
    "ESTATE",
    "ETF",
    "FAMILY",
    "FIDUCIARY",
    "FINANCIAL",
    "FOR",
    "FUND",
    "FUNDS",
    "GLOBAL",
    "GROWTH",
    "GROUP",
    "HARVEST",
    "HERITAGE",
    "IMPACT",
    "INC",
    "INCOME",
    "INCORPORATED",
    "INDEPENDENCE",
    "INDEPENDENT",
    "INFRASTRUCTURE",
    "INSURANCE",
    "INTEGRATED",
    "INTEGRITY",
    "INVESTMENT",
    "INVESTMENTS",
    "INVESTOR",
    "INVESTORS",
    "LEGACY",
    "LIMITED",
    "LLC",
    "LLP",
    "LP",
    "LTD",
    "MANAGEMENT",
    "MANAGER",
    "NETWORK",
    "PARTNERS",
    "PLANNING",
    "PORTFOLIO",
    "PRIVATE",
    "PROFESSIONAL",
    "PUBLIC",
    "QUANTITATIVE",
    "REAL",
    "RESOURCE",
    "RETIREMENT",
    "SAGE",
    "SARL",
    "SECURITIES",
    "SERVICES",
    "SOLUTIONS",
    "STRATEGIC",
    "STRATEGIES",
    "STRATEGY",
    "THE",
    "TRUST",
    "UNITED",
    "VALUE",
    "VENTURES",
    "WEALTH"
    ];
   

    LET $name_array = $name.uppercase().words().map(|$a| fn::remove_punctuation($a,""));

    
    LET $name_array = $name_array[WHERE $this != '' AND $this NOT IN $jargon_words AND $this NOT IN $geo_words];
    LET $name_array_len = $name_array.len();
    IF $name_array_len<1 THEN { 
        RETURN $name;
    } END;
    
    RETURN ($name_array.map(|$word,$index|
        IF $word.len() == 1 THEN 
            "_" + $word + '_'
        ELSE 
            $word + ' '
        END).join('').replace("__","").replace("_"," ").trim()
    );
    };



DEFINE FUNCTION OVERWRITE fn::company_token_string($name: string){
     LET $name = IF $name IS NONE THEN NONE ELSE 
        fn::clean_company_string($name)
        .replace(" ","")
    END;
    RETURN $name;
};


// Defines or overwrites a function to upsert a chief compliance officer (CCO) record and create a relationship.
DEFINE FUNCTION OVERWRITE fn::compliance_officer_upsert(
$firm:Record<firm>, // The firm the CCO is associated with.
$full_name:string, // The full name of the CCO.
$latest_adv_filing_date:datetime, // The date of the latest ADV filing.
$title:Option<string>, // The title of the CCO.
$email:Option<string> // The email address of the CCO.
)
{

    LET $full_name = fn::clean_name_string($full_name);
    // Extract first and last names from the full name.
    LET $name_parts = fn::get_name_parts_from_full_name($full_name);

    // Get or upsert the person record for the chief compliance officer.
    LET $chief_compliance_officer = fn::get_person_or_upsert(
                $full_name,
                NONE, // No specific filing context for CCO in this function.
                $name_parts["first_name"],
                $name_parts["last_name"],
                $title,
                $email
            ).id;

    // Create a relationship indicating that the person is a compliance officer for the firm,
    // effective as of the latest ADV filing date.
    RELATE $chief_compliance_officer->is_compliance_officer:[$chief_compliance_officer,$firm,$latest_adv_filing_date]->$firm  CONTENT{
                in: $chief_compliance_officer,
                out: $firm,
                as_of_latest_filing_date: $latest_adv_filing_date,
                title_at_time_of_filing: $title
            }   RETURN NONE;

    // Return the ID of the chief compliance officer person record.
    RETURN $chief_compliance_officer;
};







DEFINE FUNCTION OVERWRITE fn::firm_name_to_vector($name: string) {
    
    
    #select the vectors from the embedding table that match the words
    LET $vectors = fn::retrieve_vectors_for_firm_name($name);

    #remove any non-matches
    LET $vectors = array::filter($vectors, |$v| { RETURN $v != NONE; });
    
    #transpose the vectors to be able to average them
    LET $transposed = array::transpose($vectors);

    #sum up the individual floats in the arrays
    LET $sum_vector = $transposed.map(|$sub_array| math::sum($sub_array));

    # calculate the mean of each vector by dividing by the total number of 
    # vectors in each of the floats
    LET $mean_vector = vector::scale($sum_vector, 1.0 / array::len($vectors));

    #if the array size > 0
    RETURN IF $mean_vector.len() > 0 THEN $mean_vector ELSE array::repeat(MATH::NEG_INF,100) END;
};


DEFINE FUNCTION OVERWRITE fn::retrieve_vectors_for_firm_name($sentence:string) 
{
    LET $sentence = fn::remove_punctuation($sentence.uppercase(), " ");
    LET $words = $sentence.words();
    LET $words = array::filter($words, |$word: any| $word != '');   
    #select the vectors from the embedding table that match the words
    RETURN (SELECT VALUE type::thing('firm_name_embedding_model',$this).embedding FROM $words);
};

DEFINE  FUNCTION OVERWRITE fn::remove_punctuation($input: string,$replace_with:"" | " ") -> string {

    LET $punctuation = [
        '.', ',', '&', '(', ')', '"', "'", "+", "!", '-', "{", "}", "[", "]", ":", ";", "<", ">", "`", "/", "\\", "—", "–"
    ];
    IF $replace_with = " " THEN{
        RETURN $punctuation.fold($input,|$a, $b| 
            $a.replace($b, " ")
        );
    }ELSE{
        RETURN $punctuation.fold($input,|$a, $b| 
            $a.replace($b, "")
        );
    }END;
};