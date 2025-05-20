
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

#AUM Firm and Custodian Type
Select math::sum(assets_under_management), custodian_type, in.firm_type as firmType 
from custodian_for
where custodian_type in 
[custodian_type:PF, custodian_type:RAUM]
group by custodian_type, firmType;

#Connecting Firms via Compliance Officers
Connecting Firms Via a Compliance Officers
SELECT a,name,id,a.len() AS count, firm.{id, name} FROM (
SELECT 
<- is_compliance_officer<-person -> is_compliance_officer -> firm.{id, name} AS a,
Name,id
FROM firm WHERE firm_type = firm_type:Registered
) ORDER by count DESC;


#Vector Similarity Search
LET $name_1 = fn::firm_name_to_vector( "JP MORGAN");
LET $name_2 = fn::firm_name_to_vector( "MORGAN STANLEY");
LET $name_3 = fn::firm_name_to_vector( "DE SHAW");

RETURN [vector::similarity::cosine($name_1, $name_2)
, vector::similarity::cosine($name_1, $name_3)];


