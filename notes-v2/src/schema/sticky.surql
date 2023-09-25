DEFINE TABLE sticky SCHEMAFULL
    PERMISSIONS
        FOR create WHERE $scope = 'user'
        FOR select, update, delete WHERE author = $auth.id;

DEFINE FIELD content ON sticky TYPE string DEFAULT "";
DEFINE FIELD color ON sticky TYPE string ASSERT $value IN ['pink', 'purple'];
DEFINE FIELD author ON sticky TYPE record<user> 
    VALUE $before OR $auth.id 
    DEFAULT $auth.id;

DEFINE FIELD created ON sticky 
    VALUE $before OR time::now()
    DEFAULT time::now();
DEFINE FIELD updated ON sticky 
    VALUE time::now()
    DEFAULT time::now();