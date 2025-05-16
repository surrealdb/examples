----------------------------------------------------------------------------------
-- AMLSim Data Generation with SurrealQL (Version 3 - Schema and Feature Polish)
----------------------------------------------------------------------------------
note to self use change feeds to capture balance changes intead
----------------------------------------------------------------------------------
-- 0. SIMULATION PARAMETERS
----------------------------------------------------------------------------------
LET $total_simulation_steps = 720;
LET $base_date = time::from::unix(time::timestamp("2017-01-01T00:00:00Z"));
LET $default_min_balance = 50000.0;
LET $default_max_balance = 100000.0;
LET $default_tx_min_amount = 100.0;
LET $default_tx_max_amount = 1000.0;
LET $margin_ratio = 0.1;
LET $enable_balance_history = true; -- SET TO true TO ENABLE BALANCE HISTORY LOGGING
LET $num_initial_accounts = 20;

----------------------------------------------------------------------------------
-- 1. SCHEMA DEFINITIONS (DDL)
----------------------------------------------------------------------------------

-- Remove tables if they exist for a clean run (optional)
REMOVE TABLE account;
REMOVE TABLE party;
REMOVE TABLE transaction;
REMOVE TABLE alert;
REMOVE TABLE bank;
REMOVE TABLE account_type;
REMOVE TABLE account_status;
REMOVE TABLE currency_code;
REMOVE TABLE transaction_type_def;
REMOVE TABLE alert_type_def;
REMOVE TABLE country_code;
REMOVE TABLE business_category;
REMOVE TABLE account_balance_history;
REMOVE TABLE account_holder;

-- Define Lookup/Enum Tables
DEFINE TABLE account_type SCHEMAFULL;
DEFINE FIELD code ON account_type TYPE string ASSERT $value != NONE AND $value != "";
DEFINE FIELD name ON account_type TYPE string;
DEFINE FIELD description ON account_type TYPE option<string>;
DEFINE INDEX account_type_code_unique ON TABLE account_type COLUMNS code UNIQUE;

DEFINE TABLE account_status SCHEMAFULL;
DEFINE FIELD code ON account_status TYPE string ASSERT $value != NONE AND $value != "";
DEFINE FIELD name ON account_status TYPE string;
DEFINE FIELD description ON account_status TYPE option<string>;
DEFINE INDEX account_status_code_unique ON TABLE account_status COLUMNS code UNIQUE;

DEFINE TABLE currency_code SCHEMAFULL;
DEFINE FIELD code ON currency_code TYPE string ASSERT $value != NONE AND string::len($value) == 3;
DEFINE FIELD name ON currency_code TYPE string;
DEFINE INDEX currency_code_code_unique ON TABLE currency_code COLUMNS code UNIQUE;

DEFINE TABLE transaction_type_def SCHEMAFULL;
DEFINE FIELD code ON transaction_type_def TYPE string ASSERT $value != NONE AND $value != "";
DEFINE FIELD name ON transaction_type_def TYPE string;
DEFINE FIELD description ON transaction_type_def TYPE option<string>;
DEFINE INDEX transaction_type_def_code_unique ON TABLE transaction_type_def COLUMNS code UNIQUE;

DEFINE TABLE alert_type_def SCHEMAFULL;
DEFINE FIELD code ON alert_type_def TYPE string ASSERT $value != NONE AND $value != "";
DEFINE FIELD name ON alert_type_def TYPE string;
DEFINE FIELD description ON alert_type_def TYPE option<string>;
DEFINE INDEX alert_type_def_code_unique ON TABLE alert_type_def COLUMNS code UNIQUE;

DEFINE TABLE country_code SCHEMAFULL;
DEFINE FIELD code ON country_code TYPE string ASSERT $value != NONE AND string::len($value) == 2;
DEFINE FIELD name ON country_code TYPE string;
DEFINE INDEX country_code_code_unique ON TABLE country_code COLUMNS code UNIQUE;

DEFINE TABLE business_category SCHEMAFULL;
DEFINE FIELD code ON business_category TYPE string ASSERT $value != NONE AND $value != "";
DEFINE FIELD name ON business_category TYPE string;
DEFINE FIELD description ON business_category TYPE option<string>;
DEFINE INDEX business_category_code_unique ON TABLE business_category COLUMNS code UNIQUE;

-- Main Entity Tables
DEFINE TABLE bank SCHEMAFULL;
DEFINE FIELD bank_id ON bank TYPE string ASSERT $value != NONE AND $value != "";
DEFINE FIELD name ON bank TYPE string;
DEFINE INDEX bank_id_unique ON TABLE bank COLUMNS bank_id UNIQUE;

DEFINE TABLE account SCHEMAFULL;
DEFINE FIELD acct_id ON account TYPE string ASSERT $value != NONE AND $value != "";
DEFINE FIELD dsply_nm ON account TYPE string;
DEFINE FIELD acct_type_link ON account TYPE record<account_type>;
DEFINE FIELD acct_stat_link ON account TYPE record<account_status>;
DEFINE FIELD currency_link ON account TYPE record<currency_code>;
DEFINE FIELD initial_deposit ON account TYPE float;
DEFINE FIELD balance ON account TYPE float;
DEFINE FIELD country_link ON account TYPE record<country_code>;
DEFINE FIELD business_cat_link ON account TYPE record<business_category>;
DEFINE FIELD open_dt ON account TYPE datetime;
DEFINE FIELD close_dt ON account TYPE option<datetime>;
DEFINE FIELD is_sar ON account TYPE bool DEFAULT false;
DEFINE FIELD is_alert_candidate ON account TYPE bool DEFAULT false;
DEFINE FIELD tx_behavior_id ON account TYPE int DEFAULT 1;
DEFINE FIELD bank_details ON account TYPE record<bank>;
DEFINE INDEX acct_id_unique ON TABLE account COLUMNS acct_id UNIQUE;

DEFINE TABLE party SCHEMAFULL;
DEFINE FIELD party_id ON party TYPE string ASSERT $value != NONE AND $value != "";
DEFINE FIELD party_type ON party TYPE string ASSERT $value IN ["Individual", "Organization"];
DEFINE FIELD legal_name ON party TYPE string;
DEFINE FIELD first_name ON party TYPE option<string>;
DEFINE FIELD last_name ON party TYPE option<string>;
DEFINE FIELD street_addr ON party TYPE option<string>;
DEFINE FIELD city ON party TYPE option<string>;
DEFINE FIELD state ON party TYPE option<string>;
DEFINE FIELD zip_code ON party TYPE option<string>;
DEFINE FIELD gender ON party TYPE option<string>;
DEFINE FIELD birth_date ON party TYPE option<datetime>;
DEFINE INDEX party_id_unique ON TABLE party COLUMNS party_id UNIQUE;

DEFINE TABLE transaction SCHEMAFULL;
DEFINE FIELD tran_id ON transaction TYPE string ASSERT $value != NONE AND $value != "";
DEFINE FIELD orig_acct ON transaction TYPE record<account> ASSERT $value != NONE;
DEFINE FIELD bene_acct ON transaction TYPE record<account> ASSERT $value != NONE;
DEFINE FIELD tx_type_link ON transaction TYPE record<transaction_type_def> ASSERT $value != NONE;
DEFINE FIELD base_amt ON transaction TYPE float ASSERT $value > 0.0;
DEFINE FIELD tran_timestamp ON transaction TYPE datetime ASSERT $value != NONE;
DEFINE FIELD is_sar_tx ON transaction TYPE bool DEFAULT false;
DEFINE FIELD alert_link ON transaction TYPE option<record<alert>>;
DEFINE INDEX tran_id_unique ON TABLE transaction COLUMNS tran_id UNIQUE;

DEFINE TABLE alert SCHEMAFULL;
DEFINE FIELD alert_id ON alert TYPE string ASSERT $value != NONE AND $value != "";
DEFINE FIELD alert_type_link ON alert TYPE record<alert_type_def>;
DEFINE FIELD is_sar_alert ON alert TYPE bool DEFAULT true;
DEFINE FIELD start_step ON alert TYPE int;
DEFINE FIELD end_step ON alert TYPE int;
DEFINE FIELD min_amount_spec ON alert TYPE float;
DEFINE FIELD max_amount_spec ON alert TYPE float;
DEFINE FIELD main_account ON alert TYPE option<record<account>>;
DEFINE INDEX alert_id_unique ON TABLE alert COLUMNS alert_id UNIQUE;

-- Optional Table for Balance History
DEFINE TABLE account_balance_history SCHEMAFULL IF $enable_balance_history == true;
DEFINE FIELD account_link ON account_balance_history TYPE record<account> ASSERT $value != NONE;
DEFINE FIELD step ON account_balance_history TYPE int ASSERT $value >= 0;
DEFINE FIELD timestamp ON account_balance_history TYPE datetime ASSERT $value != NONE;
DEFINE FIELD balance_before ON account_balance_history TYPE float;
DEFINE FIELD balance_after ON account_balance_history TYPE float;
DEFINE FIELD transaction_link ON account_balance_history TYPE option<record<transaction>>;
DEFINE INDEX idx_account_step_history ON TABLE account_balance_history COLUMNS account_link, step, timestamp UNIQUE; -- Added timestamp for more uniqueness

-- Relationship table: account_holder
DEFINE TABLE account_holder SCHEMAFULL;
DEFINE FIELD in ON account_holder TYPE record<party>;
DEFINE FIELD out ON account_holder TYPE record<account>;
DEFINE FIELD role ON account_holder TYPE string DEFAULT "Primary";
DEFINE FIELD start_date ON account_holder TYPE datetime;
DEFINE FIELD end_date ON account_holder TYPE option<datetime>;
DEFINE INDEX idx_account_holder_rel ON TABLE account_holder COLUMNS in, out UNIQUE;


----------------------------------------------------------------------------------
-- 2. CREATE LOOKUP/ENUM DATA
----------------------------------------------------------------------------------
CREATE account_type:SAV CONTENT {code: "SAV", name: "Savings Account"};
CREATE account_type:CHK CONTENT {code: "CHK", name: "Checking Account"};

CREATE account_status:A CONTENT {code: "A", name: "Active"};

CREATE currency_code:USD CONTENT {code: "USD", name: "US Dollar"};

CREATE transaction_type_def:TRANSFER CONTENT {code: "TRANSFER", name: "Transfer"};
CREATE transaction_type_def:CREDIT CONTENT {code: "CREDIT", name: "Credit"};

CREATE alert_type_def:FAN_OUT CONTENT {code: "fan_out", name: "Fan Out"};
CREATE alert_type_def:FAN_IN CONTENT {code: "fan_in", name: "Fan In"};
CREATE alert_type_def:CYCLE CONTENT {code: "cycle", name: "Cycle"};

CREATE country_code:US CONTENT {code: "US", name: "United States"};

CREATE business_category:I CONTENT {code: "I", name: "Individual/Consumer"};

----------------------------------------------------------------------------------
-- 3. FUNCTION DEFINITIONS
----------------------------------------------------------------------------------

DEFINE FUNCTION fn::log_balance_change(
    $account_id: record<account>,
    $step: int,
    $timestamp: datetime,
    $bal_before: float,
    $bal_after: float,
    $tx_id: option<record<transaction>>
) {
    IF $enable_balance_history THEN {
        CREATE account_balance_history CONTENT {
            account_link: $account_id,
            step: $step,
            timestamp: $timestamp,
            balance_before: $bal_before,
            balance_after: $bal_after,
            transaction_link: $tx_id
        };
    } END;
    RETURN true;
};

DEFINE FUNCTION fn::create_single_transaction(
    $originator_account_id: record<account>, // Expecting record ID
    $beneficiary_account_id: record<account>, // Expecting record ID
    $amount: float,
    $current_step: int,
    $tx_type_link: record<transaction_type_def>,
    $is_part_of_sar: bool,
    $alert_ref: option<record<alert>>
) {
    LET $timestamp = समय::add($base_date, $current_step * 1d);

    // Fetch current balances before transaction
    LET $orig_details = (SELECT balance FROM $originator_account_id)[0];
    LET $bene_details = (SELECT balance FROM $beneficiary_account_id)[0];
    LET $orig_bal_before = $orig_details.balance OR 0.0; // Default to 0 if balance is null
    LET $bene_bal_before = $bene_details.balance OR 0.0;

    // Check if originator has enough balance
    IF $orig_bal_before < $amount THEN {
        // RETURN { error: "Insufficient balance for originator.", id: NONE }; // Or handle error differently
        // For simulation, we might allow it to go negative or just skip if strict
        // For now, we'll proceed but this is a point of simulation rule design
    } END;

    LET $tx = CREATE transaction CONTENT {
        tran_id: rand::uuid(),
        orig_acct: $originator_account_id,
        bene_acct: $beneficiary_account_id,
        base_amt: $amount,
        tran_timestamp: $timestamp,
        tx_type_link: $tx_type_link,
        is_sar_tx: $is_part_of_sar,
        alert_link: $alert_ref
    };

    LET $orig_bal_after = $orig_bal_before - $amount;
    LET $bene_bal_after = $bene_bal_before + $amount;

    UPDATE $originator_account_id SET balance = $orig_bal_after;
    UPDATE $beneficiary_account_id SET balance = $bene_bal_after;

    CALL fn::log_balance_change($originator_account_id, $current_step, $timestamp, $orig_bal_before, $orig_bal_after, $tx.id);
    CALL fn::log_balance_change($beneficiary_account_id, $current_step, $timestamp, $bene_bal_before, $bene_bal_after, $tx.id);

    IF $alert_ref != NONE THEN {
        RELATE $tx->generated_by_alert->$alert_ref;
        RELATE $alert_ref->includes_transaction->$tx;
    } END;

    RETURN $tx.id;
};


DEFINE FUNCTION fn::simulate_fan_out_fraud(
    $main_acct_id: record<account>,      // Originator account ID
    $bene_acct_ids_array: array,     // Array of beneficiary account IDs
    $amount_per_tx: float,
    $current_step: int,
    $alert_record_id: record<alert>,
    $period_range: int
) {
    LET $created_tx_ids = [];
    FOR $bene_acct_id IN $bene_acct_ids_array {
        LET $tx_step = $current_step + rand::int(0, $period_range - 1);
        LET $actual_amount = rand::float($amount_per_tx * 0.8, $amount_per_tx * 1.2);
        
        LET $tx_id = CALL fn::create_single_transaction(
            $main_acct_id,
            $bene_acct_id,
            $actual_amount,
            $tx_step,
            transaction_type_def:TRANSFER,
            true,
            $alert_record_id
        );
        IF $tx_id.id != NONE THEN { // Check if transaction was successful (e.g. if error handling was added)
            LET $created_tx_ids = array::push($created_tx_ids, $tx_id);
        }
    }
    RETURN $created_tx_ids;
};

DEFINE FUNCTION fn::simulate_fan_in_fraud(
    $orig_acct_ids_array: array,
    $main_acct_id: record<account>,
    $amount_per_tx: float,
    $current_step: int,
    $alert_record_id: record<alert>,
    $period_range: int
) {
    LET $created_tx_ids = [];
    FOR $orig_acct_id IN $orig_acct_ids_array {
        LET $tx_step = $current_step + rand::int(0, $period_range - 1);
        LET $actual_amount = rand::float($amount_per_tx * 0.8, $amount_per_tx * 1.2);

        LET $tx_id = CALL fn::create_single_transaction(
            $orig_acct_id,
            $main_acct_id,
            $actual_amount,
            $tx_step,
            transaction_type_def:TRANSFER,
            true,
            $alert_record_id
        );
        IF $tx_id.id != NONE THEN {
            LET $created_tx_ids = array::push($created_tx_ids, $tx_id);
        }
    }
    RETURN $created_tx_ids;
};


DEFINE FUNCTION fn::simulate_cycle_fraud(
    $cycle_account_ids_array: array,
    $initial_amount: float,
    $current_step: int,
    $alert_record_id: record<alert>,
    $period_range: int
) {
    LET $num_cycle_accounts = count($cycle_account_ids_array);
    IF $num_cycle_accounts < 2 THEN { RETURN []; }

    LET $created_tx_ids = [];
    LET $current_tx_amount = $initial_amount;

    FOR $i IN 0..($num_cycle_accounts - 1) {
        LET $orig_acct_id = array::at($cycle_account_ids_array, $i);
        LET $bene_idx = ($i + 1) % $num_cycle_accounts;
        LET $bene_acct_id = array::at($cycle_account_ids_array, $bene_idx);
        LET $tx_step = $current_step + rand::int(0, $period_range - 1);
        
        IF $i > 0 THEN {
            LET $current_tx_amount -= ($current_tx_amount * $margin_ratio);
        }
        LET $current_tx_amount = math::max($current_tx_amount, 0.01);

        LET $tx_id = CALL fn::create_single_transaction(
            $orig_acct_id,
            $bene_acct_id,
            $current_tx_amount,
            $tx_step,
            transaction_type_def:TRANSFER,
            true,
            $alert_record_id
        );
        IF $tx_id.id != NONE THEN {
             LET $created_tx_ids = array::push($created_tx_ids, $tx_id);
        }
    }
    RETURN $created_tx_ids;
};


----------------------------------------------------------------------------------
-- 4. INITIAL DATA POPULATION (Example)
----------------------------------------------------------------------------------
LET $default_bank_record = CREATE bank CONTENT { bank_id: "bank_default", name: "Default Central Bank"};

FOR $i IN 1..$num_initial_accounts {
    LET $acct_id_val = string::concat("ACC", $i);
    LET $initial_bal = rand::float($default_min_balance, $default_max_balance);
    LET $open_step = rand::int(0, 10);
    LET $open_date = समय::add($base_date, $open_step * 1d);

    LET $created_account = CREATE account SET
        acct_id = $acct_id_val,
        dsply_nm = string::concat("User ", $acct_id_val),
        balance = $initial_bal,
        initial_deposit = $initial_bal,
        open_dt = $open_date,
        is_alert_candidate = if rand::bool() then true else false end,
        acct_type_link = account_type:SAV,
        acct_stat_link = account_status:A,
        currency_link = currency_code:USD,
        country_link = country_code:US,
        business_cat_link = business_category:I,
        bank_details = $default_bank_record.id;

    CALL fn::log_balance_change($created_account.id, $open_step, $open_date, 0.0, $initial_bal, NONE);
};

----------------------------------------------------------------------------------
-- 5. CONCEPTUAL MAIN SIMULATION LOOP (Client-Driven Recommended)
----------------------------------------------------------------------------------
/*
-- Example of calling a fraud function (client would select accounts and parameters)
-- LET $all_accounts = SELECT id FROM account;
-- IF count($all_accounts) >= 5 THEN {
--     LET $main_fan_out_acct_id = $all_accounts[0].id;
--     LET $bene_acct_ids_for_fan_out = [$all_accounts[1].id, $all_accounts[2].id, $all_accounts[3].id];
--     LET $fan_out_alert_amount = 2000.0;
--     LET $fan_out_alert_period = 5;

--     LET $fan_out_alert_rec = CREATE alert CONTENT {
--         alert_id: rand::uuid(),
--         alert_type_link: alert_type_def:FAN_OUT,
--         is_sar_alert: true,
--         start_step: 10, end_step: 10 + $fan_out_alert_period - 1,
--         min_amount_spec: $fan_out_alert_amount, max_amount_spec: $fan_out_alert_amount,
--         main_account: $main_fan_out_acct_id
--     };
--     CALL fn::simulate_fan_out_fraud(
--         $main_fan_out_acct_id,
--         $bene_acct_ids_for_fan_out,
--         $fan_out_alert_amount,
--         10, -- current_step for the alert start
--         $fan_out_alert_rec.id,
--         $fan_out_alert_period
--     );
-- } END;

FOR $current_step IN 0..($total_simulation_steps - 1) {
    // PRINT "Processing step: ", $current_step;
    // Client-driven logic would go here to:
    // 1. Read current state of relevant accounts.
    // 2. Decide which accounts transact (normal or fraudulent).
    // 3. If fraudulent, select pattern, participants, amounts, period based on AMLSim parameters.
    // 4. Call appropriate fn::simulate_..._fraud or fn::create_single_transaction.
};
PRINT "Conceptual simulation finished after ", $total_simulation_steps, " steps.";
*/













