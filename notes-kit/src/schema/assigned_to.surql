DEFINE TABLE assigned_to SCHEMAFULL
    TYPE RELATION
        IN tag
        OUT sticky
    PERMISSIONS
        FOR create, select, update, delete 
            WHERE in.owner == $auth.id AND out.author == $auth.id;

DEFINE FIELD created ON assigned_to 
    VALUE $before OR time::now()
    DEFAULT time::now();
DEFINE FIELD updated ON assigned_to 
    VALUE time::now()
    DEFAULT time::now();