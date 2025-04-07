
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
    LET $chief_compliance_officer = fn::person_upsert(
                $firm,
                $full_name,
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
    $section_5f: option<object>)
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

        
        UPSERT $firm CONTENT{
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

        RETURN $firm;
    };




DEFINE FUNCTION OVERWRITE fn::person_upsert(
    $firm: Record<firm>,
    $full_name: string,
    $first_name: Option<string>,
    $last_name: Option<string>,
    $title: Option<string>,
    $email: Option<string>)
    {   
        UPSERT type::thing("person",[$full_name,$firm]) CONTENT{

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

    LET $signatory = fn::person_upsert(
        $firm,
        $full_name,
        $name_parts["first_name"],
        $name_parts["last_name"],
        $title
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

        UPSERT $filing CONTENT{
            filing_id: $filing_id,
            filing_firm: $firm,
            execution_type: $execution_type,
            signatory: $signatory,
        } RETURN NONE;
        
        RETURN $filing;
    };


    


DEFINE FUNCTION OVERWRITE fn::custodian_get_or_upsert(
    $name: string,
    $legal_name: string,
    $sec_number: Option<string>,
    $legal_entity_identifier: Option<string>,
    $city: Option<string>,
    $state: Option<string>,
    $country: Option<string>){
        RETURN fn::firm_get_or_upsert(
            $name,
            $legal_name,
            "SMA Custodian",
            $sec_number,
            $legal_entity_identifier,
            $city,
            $state,
            NONE,
            $country
        );
    
    };

DEFINE FUNCTION OVERWRITE fn::firm_get_or_upsert(
    $name: string,
    $legal_name: string,
    $firm_type_name_if_insert: string,
    $sec_number: Option<string>,
    $legal_entity_identifier: Option<string>,
    $city: Option<string>,
    $state: Option<string>,
    $postal_code: Option<string>,
    $country: Option<string>){
    
    LET $custodian_firm = 
        fn::find_match_for_firm  (
            $name,
            $legal_name,
            $sec_number,
            $city,
            $state,
            $country
        );
    
        
    IF $custodian_firm IS NOT NONE THEN{
        RETURN $custodian_firm;
    } ELSE {
       
        IF $sec_number IS NOT NONE THEN {
            RETURN fn::firm_upsert(
                        $name,$sec_number,$firm_type_name_if_insert,$name,$city,$state,$postal_code,$country,  {"sec_number":$sec_number}, NONE, NONE
                    ).id; 
        }ELSE{
            IF $legal_entity_identifier IS NOT NONE THEN {
                RETURN fn::firm_upsert(
                                    $name,$legal_entity_identifier,$firm_type_name_if_insert,$name,$city,$state,$postal_code,$country, NONE, NONE, NONE
                                ).id;
            }ELSE {

                RETURN fn::firm_upsert(
                                $name,$legal_name,$firm_type_name_if_insert,$name,$city,$state,$postal_code,$country, NONE, NONE, NONE
                            ).id;
            } END;
        }END;   
    }
    END;
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
        LET $filing_firm = $filing["filing_firm"];
        LET $custodian_firm = fn::custodian_get_or_upsert(
            $primary_business_name,
            $legal_name,
            $sec_number,
            $legal_entity_identifier,
            $city,
            $state,
            $country);

        
        LET $related_person = IF $legal_entity_identifier IS NONE THEN FALSE ELSE $legal_entity_identifier.lowercase() in ["yes","true","1","y"] END;
        RELATE $custodian_firm->custodian_for:[$custodian_firm,$filing_firm]->$filing_firm  CONTENT{
            in: $custodian_firm,
            out: $filing_firm,
            source_filing: $filing,
            custodian_type: custodian_type:`SMA`,
            legal_entity_identifier: $legal_entity_identifier,
            assets_under_management: $assets_under_management,
            related_person: $related_person
        } RETURN NONE; 
    };


DEFINE FUNCTION OVERWRITE fn::string_match_score($match:option<string>,$value:option<string>){
    IF $value IS NONE AND $match IS NONE THEN {
        RETURN 1;
    }
    ELSE{
        IF ($value IS NOT NONE AND $match IS NOT NONE) AND 
                ($value.lowercase() == $match.lowercase()) THEN {
                RETURN 1;
                }
        END;
    } END;
    RETURN 0;
};

DEFINE FUNCTION OVERWRITE fn::firm_match_score($name_score_1:float,$name_score_2:float,
$city_match:option<string>,$city:option<string>,
$state_match:option<string>,$state:option<string>,
$country_match:option<string>,$country:option<string>){
    LET $ft_score = $name_score_1 + $name_score_2;
    LET $city_score = fn::string_match_score($city_match,$city);
    LET $state_score = fn::string_match_score($state_match,$state);
    LET $country_score = fn::string_match_score($country_match,$country);
    
    LET $geo_factor = 4.0; #the higher the less weight to geo matching
    RETURN $ft_score * ($geo_factor + $city_score + $state_score + $country_score) / $geo_factor;
};


DEFINE FUNCTION OVERWRITE fn::find_match_for_firm(
    $name: string,
    $legal_name: string,
    $sec_number: Option<string>,
    $city: Option<string>,
    $state: Option<string>,
    $country: Option<string>){

    

    IF $sec_number IS NOT NONE THEN {
        LET $custodian_firm = type::thing("firm",$sec_number);
        IF $custodian_firm["identifier"] IS NOT NONE THEN {
            RETURN $custodian_firm;
        } END;
    } END;

    LET $custodian_firm = SELECT VALUE id FROM(
        SELECT id, fn::firm_match_score(
            search::score(1),search::score(2),
            $city,city,
            $state,state,
            $country,country
        ) AS score FROM firm WHERE 
                    (name @1@ $name OR name @2@ $legal_name) ORDER BY score DESC LIMIT 1);

    RETURN $custodian_firm[0];
};






DEFINE FUNCTION OVERWRITE fn::b_and_r_custodian_get_or_upsert(
    $name: string,
    $city: Option<string>,
    $state: Option<string>,
    $postal_code: Option<string>,
    $country: Option<string>){
        RETURN fn::firm_get_or_upsert(
            $name,
            $name,
            "Records Custodian",
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
   
        LET $filing_firm = $filing["filing_firm"];

        LET $custodian_type = fn::custodian_type($type);



        LET $custodian_firm = fn::b_and_r_custodian_get_or_upsert(
            $name,
            $city,
            $state,
            $postal_code,
            $country);

        RELATE $custodian_firm->custodian_for:[$custodian_firm,$filing_firm]->$filing_firm  CONTENT{
            in: $custodian_firm,
            out: $filing_firm,
            source_filing: $filing,
            custodian_type: $custodian_type,
            description: $description
        } RETURN NONE; 
    };

