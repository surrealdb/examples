
DEFINE FUNCTION OVERWRITE fn::get_name_parts_from_full_name(
    $full_name: string)
    {
        IF $full_name IS NONE THEN {
            RETURN {
                first_name: NONE,
                last_name: NONE
            };
        } END;


        LET $name_parts = $full_name.split(" ");
        IF array::len($name_parts) = 1 THEN {
            RETURN {
                first_name: NONE,
                last_name: $name_parts[0]
            };
        } END;
        LET $last_name = $name_parts[array::len($name_parts)-1];
        LET $first_name = array::slice($name_parts,0,array::len($name_parts)-1).join(' ');
        RETURN {
            first_name: $first_name,
            last_name: $last_name
        };
    };

DEFINE FUNCTION OVERWRITE fn::compliance_officer_upsert(
$firm:Record<firm>,
$full_name:string,
$latest_adv_filing_date:datetime,
$title:Option<string>,
$email:Option<string>
)
{
    LET $name_parts = fn::get_name_parts_from_full_name($full_name);

    LET $chief_compliance_officer = fn::get_person_or_upsert(
                $firm,
                $full_name,
                NONE,
                $name_parts["first_name"],
                $name_parts["last_name"],
                $title,
                $email
            ).id;

    RELATE $chief_compliance_officer->is_compliance_officer:[$chief_compliance_officer,$firm,$latest_adv_filing_date]->$firm  CONTENT{
                in: $chief_compliance_officer,
                out: $firm,
                as_of_latest_filing_date: $latest_adv_filing_date,
                title_at_time_of_filing: $title
            }   RETURN NONE; 

    RETURN $chief_compliance_officer;
};

DEFINE FUNCTION OVERWRITE fn::firm_type_upsert($firm_type_name:string){
    LET $firm_type = (UPSERT type::thing("firm_type",$firm_type_name)
             CONTENT{"firm_type": $firm_type_name}).id[0];
    RETURN $firm_type;
};





DEFINE FUNCTION OVERWRITE fn::firm_upsert(
    $name: string,
    $identifier: string,
    $firm_type_name: string,
    $legal_name: option<string>,
    $city: option<string>,
    $state: option<string>,
    $postal_code: option<string>,
    $country: option<string>,
    $section1: option<object>,
    $section_5d: option<object>,
    $section_5f: option<object>,
    $firm_alias: option<Record<firm_alias>>,
    )
    {  
        LET $firm_type = fn::firm_type_upsert($firm_type_name);
        LET $firm = type::thing("firm",$identifier);

        LET $chief_compliance_officer =        
            IF $section1 IS NOT NULL AND $section1["chief_compliance_officer_name"]  IS NOT NONE THEN 
                fn::compliance_officer_upsert(
                        $firm,
                        $section1["chief_compliance_officer_name"],
                        $section1["latest_adv_filing_date"],
                        $section1["chief_compliance_officer_other_titles"],
                        $section1["chief_compliance_officer_e_mail"])
            ELSE
                NONE
            END;

        
        UPSERT $firm MERGE{
            name: $name,
            identifier: $identifier,
            firm_type: $firm_type,
            legal_name: $legal_name,
            city: $city,
            state: $state,
            postal_code: $postal_code,
            country: $country,
            chief_compliance_officer: $chief_compliance_officer,
            section1: $section1,
            section_5d: $section_5d,
            section_5f: $section_5f
        } RETURN NONE;


        
        IF $firm["firm_aliases"] IS NOT NONE THEN {
            UPDATE $firm SET 
                firm_aliases = [$firm_alias]
            RETURN NONE;
        }
        ELSE IF $firm_alias IS NOT NONE THEN
        {
            UPDATE $firm SET 
                firm_aliases = firm_aliases.union($firm_alias);
            RETURN NONE;
        } END;

        RETURN $firm;
    };


DEFINE FUNCTION OVERWRITE fn::find_alias_match_for_person(
    $firm: Record<firm>,
    $full_name: string,
    $email: Option<string>){

   

    IF $email IS NOT NONE THEN {
        LET $person_alias = type::thing("person_alias",[$firm,"E:" +$email.lowercase()]);
        IF $person_alias["person"] IS NOT NONE THEN {
            RETURN $person_alias["person"];
        } END;
    } END;



    LET $person_alias = type::thing("person_alias",[$firm,"FN:" +$full_name.lowercase()]);
    IF $person_alias["person"] IS NOT NONE THEN {
        RETURN $person_alias["person"];
    } ELSE { RETURN NONE; } END;


    };


DEFINE FUNCTION OVERWRITE fn::person_alias_upsert(
    $firm: Record<firm>,
    $person: Record<person>,
    $full_name: string,
    $source_filing : Option<Record<filing>>,
    $first_name: Option<string>,
    $last_name: Option<string>,
    $title: Option<string>,
    $email: Option<string>)
    {   

        LET $identifier =
            IF $email IS NOT NONE THEN 
                [$firm,"E:" + $email.lowercase()]
            ELSE IF $full_name IS NOT NONE THEN
                [$firm,"FN:" + $full_name.lowercase()]
            END;


        UPSERT type::thing("person_alias",$identifier) MERGE{
            source_filing: $source_filing,
            firm: $firm,
            person: $person,
            full_name: $full_name,
            first_name: $first_name,
            last_name: $last_name,
            title: $title,
            email: $email
        };
        RETURN  type::thing("person",[$full_name,$firm]);
    };

DEFINE FUNCTION OVERWRITE fn::person_upsert(
    $firm: Record<firm>,
    $full_name: string,
    $first_name: Option<string>,
    $last_name: Option<string>,
    $title: Option<string>,
    $email: Option<string>)
    {   
        UPSERT type::thing("person",[$full_name,$firm]) MERGE{

            firm: $firm,
            full_name: $full_name,
            first_name: $first_name,
            last_name: $last_name,
            title: $title,
            email: $email
        };
        RETURN  type::thing("person",[$full_name,$firm]);
    };






DEFINE FUNCTION OVERWRITE fn::signatory_upsert(
$firm:Record<firm>,
$filing:Record<filing>,
$full_name:string,
$execution_date:datetime,
$title:Option<string>
)
{
   

    LET $name_parts = fn::get_name_parts_from_full_name($full_name);
    LET $signatory = fn::get_person_or_upsert(
                $firm,
                $full_name,
                $filing,
                $name_parts["first_name"],
                $name_parts["last_name"],
                $title,
                NONE
            ).id;

    RELATE $signatory->signed:[$signatory,$filing]->$filing  CONTENT{
        in: $signatory,
        out: $filing,
        execution_date: $execution_date,
        signatory_title: $title
    } RETURN NONE; 

    RETURN $signatory;
};




DEFINE FUNCTION OVERWRITE fn::execution_type_upsert($execution_type_name:string){
    LET $execution_type = (UPSERT type::thing("ia_filing_execution_type",$execution_type_name)
            CONTENT{"execution_type": $execution_type_name}).id[0];
    RETURN $execution_type;
};


DEFINE FUNCTION OVERWRITE fn::filing_upsert(
    $filing_id: int,
    $sec_number: string,
    $execution_type_name: string,
    $execution_date: datetime,
    $signatory_name: string,
    $signatory_title: string)
    {

        LET $execution_type = fn::execution_type_upsert($execution_type_name);
        LET $firm = type::thing("firm",$sec_number);
        LET $filing = type::thing("filing",$filing_id);

        LET $signatory = fn::signatory_upsert(
            $firm,
            $filing,
            $signatory_name,
            $execution_date,
            $signatory_title
        ).id;


        RELATE $firm->filed:[$firm,$filing]->$filing  CONTENT{
            in: $firm,
            out: $filing,
            execution_date: $execution_date
        } RETURN NONE; 

        UPSERT $filing MERGE{
            filing_id: $filing_id,
            firm: $firm,
            execution_type: $execution_type,
            signatory: $signatory,
        } RETURN NONE;
        
        RETURN $filing;
    };


    

DEFINE FUNCTION OVERWRITE fn::sma_custodian_get_or_upsert(
    $source_filing : Record<filing>,
    $name: string,
    $legal_name: string,
    $sec_number: Option<string>,
    $legal_entity_identifier: Option<string>,
    $city: Option<string>,
    $state: Option<string>,
    $country: Option<string>){
        RETURN fn::firm_get_or_upsert(
            $source_filing,
            $name,
            $legal_name,
            "SMA Custodian",
            $sec_number,
            $legal_entity_identifier,
            NONE,
            $city,
            $state,
            NONE,
            $country
        );
    
    };



DEFINE FUNCTION OVERWRITE fn::firm_identifier(
    $legal_name: string,
    $sec_number: Option<string>,
    $legal_entity_identifier: Option<string>,
    $cik: Option<int>
) {
    
        LET $identifier =
            IF $sec_number IS NOT NONE THEN 
                $sec_number.lowercase()
            ELSE IF $legal_entity_identifier IS NOT NONE THEN
                "LEI:" + $legal_entity_identifier.lowercase()
            ELSE IF $cik IS NOT NONE THEN
                "CIK:" + <string>$cik
            ELSE 
                "LN:" + $legal_name.lowercase()
            END;
            RETURN $identifier;
};


DEFINE FUNCTION OVERWRITE fn::firm_alias_upsert(
    $source_filing : Record<filing>,
    $name: string,
    $legal_name: string,
    $firm_type_name: string,
    $sec_number: Option<string>,
    $legal_entity_identifier: Option<string>,
    $cik: Option<int>,
    $city: Option<string>,
    $state: Option<string>,
    $postal_code: Option<string>,
    $country: Option<string>
    ){

        LET $identifier = fn::firm_identifier($legal_name, $sec_number, $legal_entity_identifier,$cik);
        LET $firm_type = fn::firm_type_upsert($firm_type_name);
        LET $firm = $source_filing["firm"];



        LET $firm_alias = type::thing("firm_alias",$identifier);
        UPSERT $firm_alias MERGE{
            source_filing: $source_filing,
            firm: $firm,
            name: $name,
            legal_name: $legal_name,
            firm_type: $firm_type,
            sec_number: $sec_number,
            legal_entity_identifier: $legal_entity_identifier,
            cik: $cik,
            city: $city,
            state: $state,
            postal_code: $postal_code,
            country: $country
        } RETURN NONE;

        RETURN $firm_alias;
    };

DEFINE FUNCTION OVERWRITE fn::firm_get_or_upsert(
    $source_filing : Record<filing>,
    $name: string,
    $legal_name: string,
    $firm_type_name_if_insert: string,
    $sec_number: Option<string>,
    $legal_entity_identifier: Option<string>,
    $cik: Option<int>,
    $city: Option<string>,
    $state: Option<string>,
    $postal_code: Option<string>,
    $country: Option<string>
    
    ){

    #search aliases
    LET $firm = fn::find_alias_match_for_firm(
            $legal_name,
            $sec_number,
            $legal_entity_identifier,
            $cik
        );

    IF $firm IS NOT NONE THEN{
        #if found then return firm
        RETURN $firm;
    } ELSE {
        #if not found search matching firms for similar match upsert firm_alias

        LET $firm_alias = fn::firm_alias_upsert(
            $source_filing,
            $name,
            $legal_name,
            $firm_type_name_if_insert,
            $sec_number,
            $legal_entity_identifier,
            $cik,
            $city,
            $state,
            $postal_code,
            $country);



        LET $firm = 
            fn::find_match_for_firm  (
                $name,
                $legal_name,
                $city,
                $state,
                $country
            );
        
            
        IF $firm IS NOT NONE THEN{
            #if found 
            RETURN $firm;
        } ELSE {

            #if not found upsert firm and return firm

            LET $identifier = fn::firm_identifier($legal_name, $sec_number, $legal_entity_identifier,$cik);

            IF $sec_number IS NOT NONE THEN {
                RETURN fn::firm_upsert(
                            $name,$identifier,$firm_type_name_if_insert,$name,$city,$state,$postal_code,$country,  {"sec_number":$sec_number}, NONE, NONE
                        ).id; 
            }ELSE{
                IF $legal_entity_identifier IS NOT NONE THEN {
                    RETURN fn::firm_upsert(
                                        $name,$identifier,$firm_type_name_if_insert,$name,$city,$state,$postal_code,$country, NONE, NONE, NONE
                                    ).id;
                }ELSE {
                    IF $cik IS NOT NONE THEN {
                        RETURN fn::firm_upsert(
                                        $name,$identifier,$firm_type_name_if_insert,$name,$city,$state,$postal_code,$country, NONE, NONE, NONE
                                    ).id;
                    } ELSE {
                        RETURN fn::firm_upsert(
                                        $name,$identifier,$firm_type_name_if_insert,$name,$city,$state,$postal_code,$country, NONE, NONE, NONE
                                    ).id;
                    } END;
                } END;
            }END;   
        }
        END;
    } END;
};




DEFINE FUNCTION OVERWRITE fn::person_match_score(
$full_name_match:string,$full_name:string,
$last_name_match:option<string>,$last_name: option<string>,
$first_name_match:option<string>,$first_name: option<string>,
$title_match:option<string>,$title:option<string>){
    LET $full_name_score = fn::string_match_score($full_name_match,$full_name);
    LET $last_name_score = fn::string_match_score($last_name_match,$last_name);
    LET $first_name_score = fn::string_match_score($first_name_match,$first_name);
    LET $title_score = fn::string_match_score($title_match,$title);

    
    LET $full_name_weight = 1.0;
    LET $last_name_weight = 0.5;
    LET $first_name_weight = 0.5;
    LET $title_weight = 0.5;
    LET $ft_score = $full_name_weight * $full_name_score +
           $last_name_weight * $last_name_score +
           $first_name_weight * $first_name_score +
           $title_weight * $title_score;
   
    RETURN $ft_score;
};


DEFINE FUNCTION OVERWRITE fn::find_match_for_person(
    $firm: Record<firm>,
    $full_name: string,
    $first_name: Option<string>,
    $last_name: Option<string>,
    $title: Option<string>){

    LET $matched_people = SELECT id, fn::person_match_score(
            $full_name,full_name,
            $last_name,last_name,
            $first_name,first_name,
            $title,title
        ) AS _score FROM person WHERE firm = $firm AND
                    (full_name @1@ $full_name OR (last_name @2@ $last_name AND first_name @3@ $first_name)) ORDER BY _score DESC;
    RETURN $matched_people.id[0];
};
    
DEFINE FUNCTION OVERWRITE fn::get_person_or_upsert(
    $firm: Record<firm>,
    $full_name: string,
    $filing:Option<Record<filing>>,
    $first_name: Option<string>,
    $last_name: Option<string>,
    $title: Option<string>,
    $email: Option<string>){
        
    #search aliases
    LET $person = fn::find_alias_match_for_person(
            $firm,
            $full_name,
            NONE
        );
    
    IF $person IS NOT NONE THEN{
        #if found then return person
        RETURN $person;
    } ELSE {
        # search for person if matched then create person alias and return person
        
        LET $person = fn::find_match_for_person(
            $firm,
            $full_name,
            $name_parts["first_name"],
            $name_parts["last_name"]).id;

        IF $person IS NOT NONE THEN{
            
            LET $person_alias = fn::person_alias_upsert(
                $firm,
                $person,
                $full_name,
                $source_filing,
                $first_name,
                $last_name,
                $title,
                $email);
            RETURN $person;
        } ELSE {

            LET $person = fn::person_upsert(
                $firm,
                $full_name,
                $first_name,
                $last_name,
                $title
            ).id;

            LET $person_alias = fn::person_alias_upsert(
                $firm,
                $person,
                $full_name,
                $source_filing,
                $first_name,
                $last_name,
                $title,
                $email);
            RETURN $person;
            
        }END;
    }END;
};

DEFINE FUNCTION OVERWRITE fn::sma_upsert(
    $filing_id: int,
    $primary_business_name: string,
    $legal_name: string,
    $sec_number: Option<string>,
    $legal_entity_identifier: Option<string>,
    $city: Option<string>,
    $state: Option<string>,
    $country: Option<string>,
    $is_related_person: Option<string>,
    $assets_under_management: Option<decimal>)
    {
        LET $filing = type::thing("filing",$filing_id);
        LET $firm = $filing["firm"];
        LET $firm = fn::sma_custodian_get_or_upsert(
            $filing,
            $primary_business_name,
            $legal_name,
            $sec_number,
            $legal_entity_identifier,
            $city,
            $state,
            $country);

        
        LET $related_person = IF $legal_entity_identifier IS NONE THEN FALSE ELSE $legal_entity_identifier.lowercase() in ["yes","true","1","y"] END;
        RELATE $firm->custodian_for:[$firm,$firm]->$firm  CONTENT{
            in: $firm,
            out: $firm,
            source_filing: $filing,
            custodian_type: custodian_type:`SMA`,
            legal_entity_identifier: $legal_entity_identifier,
            assets_under_management: $assets_under_management,
            related_person: $related_person
        } RETURN NONE; 
    };




DEFINE FUNCTION OVERWRITE fn::string_match_score($match:option<string>,$value:option<string>){
    IF $value IS NONE AND $match IS NONE THEN {
        RETURN 0.5; #neutral if both are none
    }
    ELSE{
        IF $value IS NONE OR $match IS NONE THEN { RETURN 0; }
        ELSE { RETURN string::distance::normalized_damerau_levenshtein($match,$value); }
        END ;
    } END;
};


DEFINE FUNCTION OVERWRITE fn::firm_match_score(
$legal_name_match:string,$legal_name:string,
$name_match:string,$name:string,
$city_match:option<string>,$city:option<string>,
$state_match:option<string>,$state:option<string>,
$country_match:option<string>,$country:option<string>)

{
    LET $legal_name_score = fn::string_match_score($legal_name_match,$legal_name);
    LET $name_score = fn::string_match_score($name_match,$name);
    LET $city_score = fn::string_match_score($city_match,$city);
    LET $state_score = fn::string_match_score($state_match,$state);
    LET $country_score = fn::string_match_score($country_match,$country);
    
    LET $similarity_threshold = 0.4; #1 is identical

    IF $legal_name_score<$similarity_threshold AND $name_score<$similarity_threshold THEN { RETURN NONE } END;
    
    LET $similarity_delta_factor = 0.6; #if legal name is wildly different than name

    IF $name_score = 0 THEN { RETURN NONE; } END;
    LET $score_delta = math::abs(($legal_name_score-$name_score)/$name_score);
    
    IF $score_delta > $similarity_delta_factor THEN { RETURN NONE; } END;
    
    
    LET $legal_factor = 4.0; #the higher the more weight to legal name
    LET $ft_score = $legal_factor * $legal_name_score + $name_score;

    LET $geo_factor = 4.0; #the higher the less weight to geo matching
    RETURN $ft_score * ($geo_factor + $city_score + $state_score + $country_score) / $geo_factor;
};
 
DEFINE FUNCTION OVERWRITE fn::find_match_for_firm(
    $name: string,
    $legal_name: string,
    $city: Option<string>,
    $state: Option<string>,
    $country: Option<string>){

    LET $matched_firms = SELECT * FROM 
            (
                SELECT *, fn::firm_match_score(
                        $legal_name,legal_name,
                        $name,name,
                        $city,city,
                        $state,state,
                        $country,country
                    ) AS _score FROM firm WHERE 
                                (legal_name @1@ $legal_name OR name @2@ $name)) 
                WHERE _score IS NOT NONE ORDER BY _score DESC;
    
    IF array::len($matched_firms) > 0 THEN {RETURN $matched_firms.id[0];} ELSE {RETURN NONE;} END;
    
};
DEFINE FUNCTION OVERWRITE fn::find_alias_match_for_firm(
    $legal_name: string,
    $sec_number: Option<string>,
    $legal_entity_identifier: Option<string>,
    $cik: Option<int>){

    IF $sec_number IS NOT NONE THEN {
        LET $firm_alias = type::thing("firm_alias",$sec_number);
        IF $firm_alias["firm"] IS NOT NONE THEN {
            RETURN $firm_alias["firm"];
        } END;
    } END;


    IF $legal_entity_identifier IS NOT NONE THEN {
        LET $firm_alias = type::thing("firm_alias","LEI:" +$legal_entity_identifier);
        IF $firm_alias["firm"] IS NOT NONE THEN {
            RETURN $firm_alias["firm"];
        } END;
    } END;

    IF $cik IS NOT NONE THEN {
        LET $firm_alias = type::thing("firm_alias","CIK:" + <string>$cik);
        IF $firm_alias["firm"] IS NOT NONE THEN {
            RETURN $firm_alias["firm"];
        } END;
    } END;

    LET $firm_alias = type::thing("firm_alias","LN:" + $legal_name);
    IF $firm_alias["firm"] IS NOT NONE THEN {
        RETURN $firm_alias["firm"];
    } ELSE {RETURN NONE;} END;

    };









DEFINE FUNCTION OVERWRITE fn::b_and_r_custodian_get_or_upsert(
    $source_filing : Record<filing>,
    $name: string,
    $city: Option<string>,
    $state: Option<string>,
    $postal_code: Option<string>,
    $country: Option<string>){
        RETURN fn::firm_get_or_upsert(
            $source_filing,
            $name,
            $name,
            "Records Custodian",
            NONE,
            NONE,
            NONE,
            $city,
            $state,
            $postal_code,
            $country
        );
    
    };



DEFINE FUNCTION OVERWRITE fn::custodian_type($custodian_type_name:string){
    LET $custodian_type = (UPSERT type::thing("custodian_type",$custodian_type_name)
            CONTENT{"custodian_type": $custodian_type_name}).id[0];
    RETURN $custodian_type;
};


DEFINE FUNCTION OVERWRITE fn::b_and_r_upsert(
    $filing_id: int,
    $name: string,
    $type: string,
    $city: Option<string>,
    $state: Option<string>,
    $postal_code: Option<string>,
    $country: Option<string>,
    $description: Option<string>)
    {

            
        LET $filing = type::thing("filing",$filing_id);
   
        LET $firm = $filing["firm"];

        LET $custodian_type = fn::custodian_type($type);



        LET $firm = fn::b_and_r_custodian_get_or_upsert(
            $filing,
            $name,
            $city,
            $state,
            $postal_code,
            $country);

        RELATE $firm->custodian_for:[$firm,$firm]->$firm  CONTENT{
            in: $firm,
            out: $firm,
            source_filing: $filing,
            custodian_type: $custodian_type,
            description: $description
        } RETURN NONE; 
    };

