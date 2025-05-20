----------------------------------------------------------------------------------
-- AMLSim Data Generation with SurrealQL (Version 4 - Change Feeds)

--this is non-functional and a WIP
----------------------------------------------------------------------------------

----------------------------------------------------------------------------------
-- 0. SIMULATION PARAMETERS
----------------------------------------------------------------------------------
LET $total_simulation_steps = 720;
LET $base_date = d"2017-01-01T00:00:00Z"; -- Using SurrealDB datetime literal
LET $default_min_balance = 50000.0;
LET $default_max_balance = 100000.0;
LET $default_tx_min_amount = 100.0;
LET $default_tx_max_amount = 1000.0;
LET $margin_ratio = 0.1;
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
REMOVE TABLE party_type;
REMOVE TABLE transaction_type_def;
REMOVE TABLE alert_type_def;
REMOVE TABLE country_code;
REMOVE TABLE business_category;
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

DEFINE TABLE party_type SCHEMAFULL;
DEFINE FIELD code ON party_type TYPE string ASSERT $value != NONE AND $value != "";
DEFINE FIELD name ON party_type TYPE string;
DEFINE INDEX party_type_code_unique ON TABLE party_type COLUMNS code UNIQUE;

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
DEFINE FIELD party_type_link ON party TYPE record<party_type> ASSERT $value != NONE; -- Changed
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

-- Relationship table: account_holder
DEFINE TABLE account_holder SCHEMAFULL;
DEFINE FIELD in ON account_holder TYPE record<party>;
DEFINE FIELD out ON account_holder TYPE record<account>;
DEFINE FIELD role ON account_holder TYPE string DEFAULT "Primary";
DEFINE FIELD start_date ON account_holder TYPE datetime;
DEFINE FIELD end_date ON account_holder TYPE option<datetime>;
DEFINE INDEX idx_account_holder_rel ON TABLE account_holder COLUMNS in, out UNIQUE;

-- Change Feed for Account Balance History
DEFINE CHANGEFEED cb_account_balance ON TABLE account TYPE UPDATE WHEN $before.balance != $after.balance THEN {
    "event_type": $event,
    "account_id": $after.id, -- or $after.acct_id if you prefer the business key
    "timestamp": time::now(), -- Timestamp of the change feed event
    "balance_before": $before.balance,
    "balance_after": $after.balance,
    "change_txid": $txid -- The transaction ID of this specific database change event
};
-- To consume this feed, a client application would typically connect and listen.
-- Example: LIVE SELECT * FROM changefeed:cb_account_balance;


----------------------------------------------------------------------------------
-- 2. CREATE LOOKUP/ENUM DATA
----------------------------------------------------------------------------------
CREATE account_type:SAV CONTENT {code: "SAV", name: "Savings Account"};
CREATE account_type:CHK CONTENT {code: "CHK", name: "Checking Account"};
LET $SAV_ACCT_TYPE = account_type:SAV;

CREATE account_status:A CONTENT {code: "A", name: "Active"};
LET $ACTIVE_ACCT_STATUS = account_status:A;

CREATE currency_code:USD CONTENT {code: "USD", name: "US Dollar"};
LET $USD_CURRENCY = currency_code:USD;

CREATE party_type:Individual CONTENT {code: "IND", name: "Individual"};
CREATE party_type:Organization CONTENT {code: "ORG", name: "Organization"};
LET $INDIVIDUAL_PARTY_TYPE = party_type:Individual;
LET $ORGANIZATION_PARTY_TYPE = party_type:Organization;


CREATE transaction_type_def:TRANSFER CONTENT {code: "TRANSFER", name: "Transfer"};
CREATE transaction_type_def:CREDIT CONTENT {code: "CREDIT", name: "Credit"};
LET $TRANSFER_TX_TYPE = transaction_type_def:TRANSFER;
LET $ALL_TX_TYPES = (SELECT VALUE id FROM transaction_type_def);

CREATE alert_type_def:FAN_OUT CONTENT {code: "fan_out", name: "Fan Out"};
CREATE alert_type_def:FAN_IN CONTENT {code: "fan_in", name: "Fan In"};
CREATE alert_type_def:CYCLE CONTENT {code: "cycle", name: "Cycle"};
LET $FAN_OUT_ALERT_TYPE = alert_type_def:FAN_OUT;
LET $FAN_IN_ALERT_TYPE = alert_type_def:FAN_IN;
LET $CYCLE_ALERT_TYPE = alert_type_def:CYCLE;

CREATE country_code:US CONTENT {code: "US", name: "United States"};
LET $US_COUNTRY_CODE = country_code:US;

CREATE business_category:I CONTENT {code: "I", name: "Individual/Consumer"};
LET $INDIVIDUAL_BIZ_CAT = business_category:I;

----------------------------------------------------------------------------------
-- 3. FUNCTION DEFINITIONS
----------------------------------------------------------------------------------

DEFINE FUNCTION fn::create_single_transaction(
    $originator_account_id: record<account>,
    $beneficiary_account_id: record<account>,
    $amount: float,
    $current_step: int,
    $tx_type_link: record<transaction_type_def>,
    $is_part_of_sar: bool,
    $alert_ref: option<record<alert>>
) {
    LET $timestamp = $base_date + ($current_step * 1d); // Corrected duration addition

    // Balances are updated directly. Changefeed will capture before/after.
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

    // Update balances
    UPDATE $originator_account_id SET balance -= $amount;
    UPDATE $beneficiary_account_id SET balance += $amount;

    IF $alert_ref != NONE THEN {
        RELATE $tx->generated_by_alert->$alert_ref;
        RELATE $alert_ref->includes_transaction->$tx;
    } END;

    RETURN $tx.id;
};


DEFINE FUNCTION fn::simulate_fan_out_fraud(
    $main_acct_id: record<account>,
    $bene_acct_ids_array: array,
    $amount_per_tx: float,
    $current_step: int,
    $alert_record_id: record<alert>,
    $period_range: int
) {
    LET $created_tx_ids = [];
    FOR $bene_acct_id IN $bene_acct_ids_array {
        LET $tx_step = $current_step + rand::int(0, $period_range - 1);
        LET $actual_amount = rand::float($amount_per_tx * 0.8, $amount_per_tx * 1.2);
        
        // It's good practice to check balance before calling, or handle potential errors if fn::create_single_transaction could fail
        // For simplicity here, we assume the calling logic ensures $main_acct_id has enough funds for all legs.
        LET $tx_id_obj = CALL fn::create_single_transaction(
            $main_acct_id,
            $bene_acct_id,
            $actual_amount,
            $tx_step,
            $TRANSFER_TX_TYPE,
            true,
            $alert_record_id
        );
        // Assuming fn::create_single_transaction returns the ID directly, not an object {id: ...}
        // If it returns an object like { id: record_id }, then use $tx_id_obj.id
        IF type::is::record($tx_id_obj) THEN # Check if $tx_id_obj is a record
             LET $created_tx_ids = array::push($created_tx_ids, $tx_id_obj);
        END;

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

        LET $tx_id_obj = CALL fn::create_single_transaction(
            $orig_acct_id,
            $main_acct_id,
            $actual_amount,
            $tx_step,
            $TRANSFER_TX_TYPE,
            true,
            $alert_record_id
        );
        IF type::is::record($tx_id_obj) THEN
            LET $created_tx_ids = array::push($created_tx_ids, $tx_id_obj);
        END;
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

        LET $tx_id_obj = CALL fn::create_single_transaction(
            $orig_acct_id,
            $bene_acct_id,
            $current_tx_amount,
            $tx_step,
            $TRANSFER_TX_TYPE,
            true,
            $alert_record_id
        );
        IF type::is::record($tx_id_obj) THEN
             LET $created_tx_ids = array::push($created_tx_ids, $tx_id_obj);
        END;
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
    LET $open_date = $base_date + ($open_step * 1d); // Corrected duration addition

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
    -- Initial balance is set at creation, changefeed will capture this if it's an UPDATE after an initial 0.
    -- Or, if you want to explicitly log the "deposit" that sets the initial balance:
    -- (This would require a "source" for the initial deposit, e.g. a special bank or 'cash')
};

----------------------------------------------------------------------------------
-- 5. CONCEPTUAL MAIN SIMULATION LOOP (Client-Driven Recommended)
----------------------------------------------------------------------------------
/*
-- Example of calling a fraud function (client would select accounts and parameters)
LET $all_accounts_for_sim = (SELECT VALUE id FROM account); // Get array of record IDs

IF count($all_accounts_for_sim) >= 5 THEN {
    LET $main_fan_out_acct_id_for_sim = $all_accounts_for_sim[0];
    LET $bene_acct_ids_for_fan_out_sim = [$all_accounts_for_sim[1], $all_accounts_for_sim[2], $all_accounts_for_sim[3]];
    LET $fan_out_alert_amount_sim = 2000.0;
    LET $fan_out_alert_period_sim = 5;

    LET $fan_out_alert_rec_sim = CREATE alert CONTENT {
        alert_id: rand::uuid(),
        alert_type_link: $FAN_OUT_ALERT_TYPE,
        is_sar_alert: true,
        start_step: 10, end_step: 10 + $fan_out_alert_period_sim - 1,
        min_amount_spec: $fan_out_alert_amount_sim, max_amount_spec: $fan_out_alert_amount_sim,
        main_account: $main_fan_out_acct_id_for_sim
    };
    // Link alert to accounts (can be done via transaction links too)
    RELATE $fan_out_alert_rec_sim->alerted_account->$main_fan_out_acct_id_for_sim;
    FOR $b_id IN $bene_acct_ids_for_fan_out_sim { RELATE $fan_out_alert_rec_sim->alerted_account->$b_id; };


    CALL fn::simulate_fan_out_fraud(
        $main_fan_out_acct_id_for_sim,
        $bene_acct_ids_for_fan_out_sim,
        $fan_out_alert_amount_sim,
        10, // current_step for the alert start
        $fan_out_alert_rec_sim.id,
        $fan_out_alert_period_sim
    );
} END;


FOR $current_step IN 0..($total_simulation_steps - 1) {
    // PRINT "Processing step: ", $current_step;

    // --- Section A: Trigger Fraudulent Patterns (Example: Cycle) ---
    IF $current_step % 70 == 10 THEN { // Trigger cycle at specific steps
        LET $cycle_size = rand::int(3, 4);
        LET $cycle_candidate_acct_ids = (SELECT VALUE id FROM account WHERE balance > 1000 AND is_alert_candidate = true ORDER BY rand() LIMIT $cycle_size);

        IF count($cycle_candidate_acct_ids) == $cycle_size THEN {
            LET $cycle_alert_amount = rand::float(500, 1500);
            LET $cycle_alert_period = rand::int(3, 8);

            LET $cycle_alert_rec = CREATE alert CONTENT {
                alert_id: rand::uuid(),
                alert_type_link: $CYCLE_ALERT_TYPE,
                is_sar_alert: true,
                start_step: $current_step,
                end_step: $current_step + $cycle_alert_period - 1,
                min_amount_spec: $cycle_alert_amount,
                max_amount_spec: $cycle_alert_amount
            };
            FOR $c_id IN $cycle_candidate_acct_ids { RELATE $cycle_alert_rec->alerted_account->$c_id; };

            CALL fn::simulate_cycle_fraud(
                $cycle_candidate_acct_ids,
                $cycle_alert_amount,
                $current_step,
                $cycle_alert_rec.id,
                $cycle_alert_period
            );
        }
    } END;


    // --- Section B: Normal Transactions ---
    LET $num_normal_tx_per_step = rand::int(1, $num_initial_accounts / 4); // Number of normal transactions this step
    FOR $tx_i IN 1..$num_normal_tx_per_step {
        LET $originator_candidates_normal = (SELECT id, balance FROM account WHERE balance > 200.0 ORDER BY rand() LIMIT 1);
        IF count($originator_candidates_normal) > 0 THEN {
            LET $originator_normal_rec = $originator_candidates_normal[0];
            LET $beneficiary_candidates_normal = (SELECT id FROM account WHERE id != $originator_normal_rec.id ORDER BY rand() LIMIT 1);

            IF count($beneficiary_candidates_normal) > 0 THEN {
                LET $beneficiary_normal_id = $beneficiary_candidates_normal[0].id;
                LET $normal_amount = rand::float(10.0, math::min(200.0, $originator_normal_rec.balance * 0.02)); // Smaller % for normal

                IF $normal_amount >= 1.0 AND $originator_normal_rec.balance >= $normal_amount THEN {
                    CALL fn::create_single_transaction(
                        $originator_normal_rec.id,
                        $beneficiary_normal_id,
                        $normal_amount,
                        $current_step,
                        array::at($ALL_TX_TYPES, rand::int(0, count($ALL_TX_TYPES)-1)),
                        false,
                        NONE
                    );
                }
            }
        }
    };
};




















