
#graph exploration
LET $name_1 = fn::firm_name_to_vector( "JP MORGAN");
LET $name_2 = fn::firm_name_to_vector( "MORGAN STANLEY");
LET $name_3 = fn::firm_name_to_vector( "DE SHAW");
SELECT 
     name as _name,
     array::transpose([->custodian_for->firm.{name,id},
            ->custodian_for.{assets_under_management,custodian_type}])
         AS first_hop,

     array::transpose([->custodian_for->firm->custodian_for->firm.{name,id},
            ->custodian_for->firm->custodian_for.{assets_under_management,custodian_type}])
         AS second_hop,

     array::transpose([->custodian_for->firm->custodian_for->firm->custodian_for->firm.{name,id},
            ->custodian_for->firm->custodian_for->firm->custodian_for.{assets_under_management,custodian_type}])
         AS third_hop
FROM firm
WHERE name_embedding <|5,50|> $name_1 FETCH a;






