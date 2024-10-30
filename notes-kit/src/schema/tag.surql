DEFINE TABLE tag SCHEMAFULL
    PERMISSIONS
        FOR create WHERE $access = 'user'
        FOR select, update, delete WHERE owner = $auth.id;

DEFINE FIELD name ON tag TYPE string ASSERT string::len($value) > 0;
DEFINE FIELD owner ON tag TYPE record<user> 
    VALUE $before OR $auth.id 
    DEFAULT $auth.id;

DEFINE FIELD created ON tag 
    VALUE $before OR time::now()
    DEFAULT time::now();
DEFINE FIELD updated ON tag 
    VALUE time::now()
    DEFAULT time::now();

DEFINE EVENT removal ON tag WHEN $event = "DELETE" THEN {
    DELETE $before.id->assigned_to;
};
