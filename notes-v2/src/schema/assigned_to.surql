DEFINE TABLE assigned_to SCHEMAFULL
    PERMISSIONS
        FOR create, select, update, delete 
            WHERE in.owner == $auth.id AND out.author == $auth.id;

DEFINE FIELD in ON assigned_to TYPE record<tag>;
DEFINE FIELD out ON assigned_to TYPE record<sticky>;

DEFINE FIELD created ON assigned_to 
    VALUE $before OR time::now()
    DEFAULT time::now();
DEFINE FIELD updated ON assigned_to 
    VALUE time::now()
    DEFAULT time::now();