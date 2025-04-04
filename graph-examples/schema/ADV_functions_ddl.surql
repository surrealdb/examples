
DEFINE FUNCTION OVERWRITE fn::firm_upsert(
    $name: string,
    $identifier: string,
    $firm_type: string,
    $legal_name: option<string>,
    $city: option<string>,
    $state: option<string>,
    $country: option<string>,
    $section1: option<object>,
    $section_5d: option<object>,
    $section_5f: option<object>)
    {


        LET $firm_type_record = (UPSERT type::thing("firm_type",$firm_type)
             CONTENT{"firm_type": $firm_type}).id[0];


        UPSERT type::thing("firm",$identifier) CONTENT{

            name: $name,
            identifier: $identifier,
            firm_type: $firm_type_record,
            legal_name: $legal_name,
            city: $city,
            state: $state,
            country: $country,
            section1: $section1,
            section_5d: $section_5d,
            section_5f: $section_5f
        } RETURN NONE;
    };
