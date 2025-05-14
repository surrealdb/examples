----------------------------------------------------------------------------------
-- AMLSim Data Generation with SurrealQL (Refined Schema)
----------------------------------------------------------------------------------

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
REMOVE TABLE transaction_type_def; -- Renamed to avoid conflict with 'transaction' table
REMOVE TABLE alert_type_def;     -- Renamed
REMOVE TABLE country_code;
REMOVE TABLE business_category;


-- Define Lookup/Enum Tables
DEFINE TABLE account_type SCHEMAFULL;
DEFINE FIELD id ON account_type TYPE record<account_type>; -- Self-referential ID as string
DEFINE FIELD code ON account_type TYPE string ASSERT $value != NONE AND $value != "";
DEFINE INDEX account_type_code_unique ON account_type COLUMNS code UNIQUE;
DEFINE FIELD name ON account_type TYPE string;
DEFINE FIELD description ON account_type TYPE option<string>;

DEFINE TABLE account_status SCHEMAFULL;
DEFINE FIELD id ON account_status TYPE record<account_status>;
DEFINE FIELD code ON account_status TYPE string ASSERT $value != NONE AND $value != "";
DEFINE INDEX account_status_code_unique ON account_status COLUMNS code UNIQUE;
DEFINE FIELD name ON account_status TYPE string;
DEFINE FIELD description ON account_status TYPE option<string>;

DEFINE TABLE currency_code SCHEMAFULL;
DEFINE FIELD id ON currency_code TYPE record<currency_code>;
DEFINE FIELD code ON currency_code TYPE string ASSERT $value != NONE AND string::len($value) == 3;
DEFINE INDEX currency_code_code_unique ON currency_code COLUMNS code UNIQUE;
DEFINE FIELD name ON currency_code TYPE string;

DEFINE TABLE transaction_type_def SCHEMAFULL; -- Represents the definition of a transaction type
DEFINE FIELD id ON transaction_type_def TYPE record<transaction_type_def>;
DEFINE FIELD code ON transaction_type_def TYPE string ASSERT $value != NONE AND $value != "";
DEFINE INDEX transaction_type_def_code_unique ON transaction_type_def COLUMNS code UNIQUE;
DEFINE FIELD name ON transaction_type_def TYPE string;
DEFINE FIELD description ON transaction_type_def TYPE option<string>;

DEFINE TABLE alert_type_def SCHEMAFULL; -- Represents the definition of an AML alert type/reason
DEFINE FIELD id ON alert_type_def TYPE record<alert_type_def>;
DEFINE FIELD code ON alert_type_def TYPE string ASSERT $value != NONE AND $value != ""; -- e.g., "fan_in", "cycle"
DEFINE INDEX alert_type_def_code_unique ON alert_type_def COLUMNS code UNIQUE;
DEFINE FIELD name ON alert_type_def TYPE string;
DEFINE FIELD description ON alert_type_def TYPE option<string>;

DEFINE TABLE country_code SCHEMAFULL;
DEFINE FIELD id ON country_code TYPE record<country_code>;
DEFINE FIELD code ON country_code TYPE string ASSERT $value != NONE AND string::len($value) == 2; -- ISO 3166-1 alpha-2
DEFINE INDEX country_code_code_unique ON country_code COLUMNS code UNIQUE;
DEFINE FIELD name ON country_code TYPE string;

DEFINE TABLE business_category SCHEMAFULL;
DEFINE FIELD id ON business_category TYPE record<business_category>;
DEFINE FIELD code ON business_category TYPE string ASSERT $value != NONE AND $value != "";
DEFINE INDEX business_category_code_unique ON business_category COLUMNS code UNIQUE;
DEFINE FIELD name ON business_category TYPE string;
DEFINE FIELD description ON business_category TYPE option<string>;


-- Main Entity Tables
DEFINE TABLE bank SCHEMAFULL;
DEFINE FIELD bank_id ON bank TYPE string ASSERT $value != NONE AND $value != "";
DEFINE INDEX bank_id_unique ON bank COLUMNS bank_id UNIQUE;
DEFINE FIELD name ON bank TYPE string;

DEFINE TABLE account SCHEMAFULL;
DEFINE FIELD acct_id ON account TYPE string ASSERT $value != NONE AND $value != "";
DEFINE INDEX acct_id_unique ON account COLUMNS acct_id UNIQUE;
DEFINE FIELD dsply_nm ON account TYPE string;
DEFINE FIELD acct_type_link ON account TYPE record<account_type>; -- Changed
DEFINE FIELD acct_stat_link ON account TYPE record<account_status>; -- Changed
DEFINE FIELD currency_link ON account TYPE record<currency_code>; -- Changed
DEFINE FIELD initial_deposit ON account TYPE float;
DEFINE FIELD balance ON account TYPE float;
DEFINE FIELD country_link ON account TYPE record<country_code>; -- Changed
DEFINE FIELD business_cat_link ON account TYPE record<business_category>; -- Changed
DEFINE FIELD open_dt ON account TYPE datetime;
DEFINE FIELD close_dt ON account TYPE option<datetime>;
DEFINE FIELD is_sar ON account TYPE bool DEFAULT false;
DEFINE FIELD is_alert_candidate ON account TYPE bool DEFAULT false;
DEFINE FIELD tx_behavior_id ON account TYPE int DEFAULT 1;
DEFINE FIELD bank_details ON account TYPE record<bank>;

DEFINE TABLE party SCHEMAFULL;
DEFINE FIELD party_id ON party TYPE string ASSERT $value != NONE AND $value != "";
DEFINE INDEX party_id_unique ON party COLUMNS party_id UNIQUE;
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

DEFINE TABLE transaction SCHEMAFULL;
DEFINE FIELD tran_id ON transaction TYPE string ASSERT $value != NONE AND $value != "";
DEFINE INDEX tran_id_unique ON transaction COLUMNS tran_id UNIQUE;
DEFINE FIELD orig_acct ON transaction TYPE record<account> ASSERT $value != NONE;
DEFINE FIELD bene_acct ON transaction TYPE record<account> ASSERT $value != NONE;
DEFINE FIELD tx_type_link ON transaction TYPE record<transaction_type_def> ASSERT $value != NONE; -- Changed
DEFINE FIELD base_amt ON transaction TYPE float ASSERT $value > 0;
DEFINE FIELD tran_timestamp ON transaction TYPE datetime ASSERT $value != NONE;
DEFINE FIELD is_sar_tx ON transaction TYPE bool DEFAULT false;
DEFINE FIELD alert_link ON transaction TYPE option<record<alert)>;

DEFINE TABLE alert SCHEMAFULL;
DEFINE FIELD alert_id ON alert TYPE string ASSERT $value != NONE AND $value != "";
DEFINE INDEX alert_id_unique ON alert COLUMNS alert_id UNIQUE;
DEFINE FIELD alert_type_link ON alert TYPE record<alert_type_def>; -- Changed
DEFINE FIELD is_sar_alert ON alert TYPE bool DEFAULT true;
DEFINE FIELD start_step ON alert TYPE int;
DEFINE FIELD end_step ON alert TYPE int;
DEFINE FIELD min_amount_spec ON alert TYPE float;
DEFINE FIELD max_amount_spec ON alert TYPE float;
DEFINE FIELD main_account ON alert TYPE option<record<account)>;

-- Relationship table: account_holder (Connects party to account)
DEFINE TABLE account_holder SCHEMAFULL;
DEFINE FIELD in ON account_holder TYPE record<party>;
DEFINE FIELD out ON account_holder TYPE record<account>;
DEFINE FIELD role ON account_holder TYPE string DEFAULT "Primary"; -- e.g., Primary, Beneficiary, Signatory
DEFINE FIELD start_date ON account_holder TYPE datetime;
DEFINE FIELD end_date ON account_holder TYPE option<datetime>;
DEFINE INDEX idx_account_holder ON account_holder COLUMNS in, out UNIQUE;


----------------------------------------------------------------------------------
-- 2. GLOBAL PARAMETERS
----------------------------------------------------------------------------------
LET $total_simulation_steps = 720;
LET $base_date = time::from::unix(time::timestamp("2017-01-01T00:00:00Z"));
LET $default_min_balance = 50000.0;
LET $default_max_balance = 100000.0;
LET $default_tx_min_amount = 100.0;
LET $default_tx_max_amount = 1000.0;
LET $margin_ratio = 0.1;

----------------------------------------------------------------------------------
-- 2.1 CREATE LOOKUP/ENUM DATA
----------------------------------------------------------------------------------
-- Account Types (corresponds to 'type' in original schema.json account)
CREATE account_type:SAV CONTENT {code: "SAV", name: "Savings Account"};
CREATE account_type:CHK CONTENT {code: "CHK", name: "Checking Account"};
CREATE account_type:INV CONTENT {code: "INV", name: "Investment Account"};
LET $SAV_ACCT_TYPE = account_type:SAV;

-- Account Statuses
CREATE account_status:A CONTENT {code: "A", name: "Active"};
CREATE account_status:I CONTENT {code: "I", name: "Inactive"};
CREATE account_status:C CONTENT {code: "C", name: "Closed"};
LET $ACTIVE_ACCT_STATUS = account_status:A;

-- Currencies
CREATE currency_code:USD CONTENT {code: "USD", name: "US Dollar"};
CREATE currency_code:EUR CONTENT {code: "EUR", name: "Euro"};
LET $USD_CURRENCY = currency_code:USD;

-- Transaction Types (based on AMLSim's transactionType.csv)
CREATE transaction_type_def:TRANSFER CONTENT {code: "TRANSFER", name: "Transfer"};
CREATE transaction_type_def:CREDIT CONTENT {code: "CREDIT", name: "Credit"};
CREATE transaction_type_def:DEBIT CONTENT {code: "DEBIT", name: "Debit"};
CREATE transaction_type_def:CASHIN CONTENT {code: "CASH-IN", name: "Cash In"};
CREATE transaction_type_def:CASHOUT CONTENT {code: "CASH-OUT", name: "Cash Out"};
LET $TRANSFER_TX_TYPE = transaction_type_def:TRANSFER;

-- Alert Types (based on AMLSim's alertPatterns.csv 'type' column)
CREATE alert_type_def:FAN_IN CONTENT {code: "fan_in", name: "Fan In"};
CREATE alert_type_def:FAN_OUT CONTENT {code: "fan_out", name: "Fan Out"};
CREATE alert_type_def:CYCLE CONTENT {code: "cycle", name: "Cycle"};
CREATE alert_type_def:BIPARTITE CONTENT {code: "bipartite", name: "Bipartite"};
CREATE alert_type_def:STACK CONTENT {code: "stack", name: "Stack"};
CREATE alert_type_def:RANDOM_ALERT CONTENT {code: "random", name: "Random Alert Pattern"}; -- Renamed from just "random"
CREATE alert_type_def:SCATTER_GATHER CONTENT {code: "scatter_gather", name: "Scatter Gather"};
CREATE alert_type_def:GATHER_SCATTER CONTENT {code: "gather_scatter", name: "Gather Scatter"};
LET $FAN_OUT_ALERT_TYPE = alert_type_def:FAN_OUT;
LET $FAN_IN_ALERT_TYPE = alert_type_def:FAN_IN;
LET $CYCLE_ALERT_TYPE = alert_type_def:CYCLE;

-- Country Codes
CREATE country_code:US CONTENT {code: "US", name: "United States"};
CREATE country_code:CA CONTENT {code: "CA", name: "Canada"};
CREATE country_code:GB CONTENT {code: "GB", name: "United Kingdom"};
LET $US_COUNTRY_CODE = country_code:US;

-- Business Categories (corresponds to 'business_type' in accounts.csv param)
CREATE business_category:I CONTENT {code: "I", name: "Individual/Consumer"};
CREATE business_category:SMB CONTENT {code: "SMB", name: "Small and Medium Business"};
CREATE business_category:CORP CONTENT {code: "CORP", name: "Corporate"};
LET $INDIVIDUAL_BIZ_CAT = business_category:I;


----------------------------------------------------------------------------------
-- 3. FUNCTION DEFINITIONS
----------------------------------------------------------------------------------

DEFINE FUNCTION fn::create_normal_transaction(
    $originator_account: record<account>,
    $beneficiary_account: record<account>,
    $amount: float,
    $current_step: int,
    $tx_type_link: record<transaction_type_def>
) {
    LET $timestamp = समय::add($base_date, $current_step * 1d);

    LET $tx = CREATE transaction CONTENT {
        tran_id: rand::uuid(),
        orig_acct: $originator_account,
        bene_acct: $beneficiary_account,
        base_amt: $amount,
        tran_timestamp: $timestamp,
        tx_type_link: $tx_type_link,
        is_sar_tx: false,
        alert_link: NONE
    };

    UPDATE $originator_account SET balance -= $amount;
    UPDATE $beneficiary_account SET balance += $amount;

    RETURN $tx.id;
};


DEFINE FUNCTION fn::simulate_fan_out_fraud(
    $main_acct: record<account>,
    $bene_accts_array: array<record<account>>,
    $amount_per_tx: float,
    $current_step: int,
    $alert_record: record<alert>,
    $period_range: int
) {
    LET $created_tx_ids = [];
    FOR $bene_acct IN $bene_accts_array {
        LET $tx_step = $current_step + rand::int(0, $period_range - 1);
        LET $timestamp = समय::add($base_date, $tx_step * 1d);
        LET $actual_amount = rand::float($amount_per_tx * 0.8, $amount_per_tx * 1.2);

        IF $main_acct.balance >= $actual_amount THEN {
            LET $tx = CREATE transaction CONTENT {
                tran_id: rand::uuid(),
                orig_acct: $main_acct,
                bene_acct: $bene_acct,
                base_amt: $actual_amount,
                tran_timestamp: $timestamp,
                tx_type_link: $TRANSFER_TX_TYPE,
                is_sar_tx: true,
                alert_link: $alert_record.id
            };
            UPDATE $main_acct SET balance -= $actual_amount;
            UPDATE $bene_acct SET balance += $actual_amount;
            LET $created_tx_ids = array::push($created_tx_ids, $tx.id);
            RELATE $tx->generated_by_alert->$alert_record;
            RELATE $alert_record->includes_transaction->$tx;
        }
    }
    RETURN $created_tx_ids;
};

DEFINE FUNCTION fn::simulate_fan_in_fraud(
    $orig_accts_array: array<record<account>>,
    $main_acct: record<account>,
    $amount_per_tx: float,
    $current_step: int,
    $alert_record: record<alert>,
    $period_range: int
) {
    LET $created_tx_ids = [];
    FOR $orig_acct IN $orig_accts_array {
        LET $tx_step = $current_step + rand::int(0, $period_range - 1);
        LET $timestamp = समय::add($base_date, $tx_step * 1d);
        LET $actual_amount = rand::float($amount_per_tx * 0.8, $amount_per_tx * 1.2);

        IF $orig_acct.balance >= $actual_amount THEN {
            LET $tx = CREATE transaction CONTENT {
                tran_id: rand::uuid(),
                orig_acct: $orig_acct,
                bene_acct: $main_acct,
                base_amt: $actual_amount,
                tran_timestamp: $timestamp,
                tx_type_link: $TRANSFER_TX_TYPE,
                is_sar_tx: true,
                alert_link: $alert_record.id
            };
            UPDATE $orig_acct SET balance -= $actual_amount;
            UPDATE $main_acct SET balance += $actual_amount;
            LET $created_tx_ids = array::push($created_tx_ids, $tx.id);
            RELATE $tx->generated_by_alert->$alert_record;
            RELATE $alert_record->includes_transaction->$tx;
        }
    }
    RETURN $created_tx_ids;
};


DEFINE FUNCTION fn::simulate_cycle_fraud(
    $cycle_accounts_array: array<record<account>>,
    $initial_amount: float,
    $current_step: int,
    $alert_record: record<alert>,
    $period_range: int
) {
    LET $num_cycle_accounts = count($cycle_accounts_array);
    IF $num_cycle_accounts < 2 THEN { RETURN []; }

    LET $created_tx_ids = [];
    LET $current_tx_amount = $initial_amount;

    FOR $i IN 0..($num_cycle_accounts - 1) {
        LET $orig_acct_record = array::at($cycle_accounts_array, $i);
        LET $bene_idx = ($i + 1) % $num_cycle_accounts;
        LET $bene_acct_record = array::at($cycle_accounts_array, $bene_idx);
        LET $tx_step = $current_step + rand::int(0, $period_range - 1);
        LET $timestamp = समय::add($base_date, $tx_step * 1d);
        
        IF $i > 0 THEN {
            LET $current_tx_amount -= ($current_tx_amount * $margin_ratio);
        }
        LET $current_tx_amount = math::max($current_tx_amount, 1.0);

        IF $orig_acct_record.balance >= $current_tx_amount THEN {
            LET $tx = CREATE transaction CONTENT {
                tran_id: rand::uuid(),
                orig_acct: $orig_acct_record.id,
                bene_acct: $bene_acct_record.id,
                base_amt: $current_tx_amount,
                tran_timestamp: $timestamp,
                tx_type_link: $TRANSFER_TX_TYPE,
                is_sar_tx: true,
                alert_link: $alert_record.id
            };
            UPDATE $orig_acct_record.id SET balance -= $current_tx_amount;
            UPDATE $bene_acct_record.id SET balance += $current_tx_amount;
            LET $created_tx_ids = array::push($created_tx_ids, $tx.id);
            RELATE $tx->generated_by_alert->$alert_record;
            RELATE $alert_record->includes_transaction->$tx;
        } ELSE {
            // Not enough balance, skip this leg of the cycle or handle as error
            // PRINT "Account ", $orig_acct_record.acct_id, " has insufficient funds for cycle leg.";
        }
    }
    RETURN $created_tx_ids;
};


----------------------------------------------------------------------------------
-- 4. INITIAL DATA POPULATION (Example)
----------------------------------------------------------------------------------

-- Create a default bank
LET $default_bank_record = CREATE bank CONTENT { bank_id: "bank_default", name: "Default Central Bank"};

-- Create a few accounts for testing
LET $num_initial_accounts = 20;
FOR $i IN 1..$num_initial_accounts {
    LET $acct_id_val = string::concat("ACC", $i);
    LET $initial_bal = rand::float($default_min_balance, $default_max_balance);
    LET $open_step = rand::int(0, 50);
    CREATE account CONTENT {
        acct_id: $acct_id_val,
        dsply_nm: string::concat("User ", $acct_id_val),
        balance: $initial_bal,
        initial_deposit: $initial_bal,
        open_dt: समय::add($base_date, $open_step * 1d),
        is_alert_candidate: if rand::bool() then true else false end,
        acct_type_link: $SAV_ACCT_TYPE,
        acct_stat_link: $ACTIVE_ACCT_STATUS,
        currency_link: $USD_CURRENCY,
        country_link: $US_COUNTRY_CODE,
        business_cat_link: $INDIVIDUAL_BIZ_CAT,
        bank_details: $default_bank_record.id
    };
};

----------------------------------------------------------------------------------
-- 5. CONCEPTUAL MAIN SIMULATION LOOP (Best driven by a client application)
----------------------------------------------------------------------------------
/*

FOR $current_step IN 0..($total_simulation_steps - 1) {

    // Section A: Trigger Fraudulent Patterns (Example: Fan-Out)
    IF $current_step % 50 == 0 AND $current_step > 0 THEN {
        LET $main_candidates = (SELECT * FROM account WHERE balance > 2 * $default_tx_max_amount AND is_alert_candidate = true ORDER BY rand() LIMIT 1);
        IF count($main_candidates) > 0 THEN {
            LET $main_fan_out_acct_record = $main_candidates[0];
            LET $num_benes = rand::int(3, 7);
            LET $bene_candidate_records = (SELECT * FROM account WHERE id != $main_fan_out_acct_record.id ORDER BY rand() LIMIT $num_benes);

            IF count($bene_candidate_records) == $num_benes THEN {
                LET $alert_amount = rand::float($default_tx_min_amount, $default_tx_max_amount);
                LET $alert_period = rand::int(5, 15);

                LET $fan_out_alert_record = CREATE alert CONTENT {
                    alert_id: rand::uuid(),
                    alert_type_link: $FAN_OUT_ALERT_TYPE,
                    is_sar_alert: true,
                    start_step: $current_step,
                    end_step: $current_step + $alert_period -1,
                    min_amount_spec: $alert_amount,
                    max_amount_spec: $alert_amount,
                    main_account: $main_fan_out_acct_record.id
                };
                RELATE $fan_out_alert_record->involves_account->$main_fan_out_acct_record.id;
                FOR $b_rec IN $bene_candidate_records { RELATE $fan_out_alert_record->involves_account->$b_rec.id; };

                CALL fn::simulate_fan_out_fraud(
                    $main_fan_out_acct_record.id,
                    $bene_candidate_records, // Pass array of full records
                    $alert_amount,
                    $current_step,
                    $fan_out_alert_record.id,
                    $alert_period
                );
            }
        }
    } END;

    // Section B: Normal Transactions
    LET $active_accounts_for_normal_tx = (SELECT * FROM account WHERE balance > ($default_tx_min_amount / 2) ORDER BY rand() LIMIT ($num_initial_accounts / 4));
    FOR $originator_rec IN $active_accounts_for_normal_tx {
        IF $originator_rec.balance > $default_tx_min_amount THEN {
            LET $num_normal_tx_this_step = rand::int(0, 1);
            IF $num_normal_tx_this_step > 0 THEN {
                LET $beneficiary_candidates_normal_recs = (SELECT * FROM account WHERE id != $originator_rec.id ORDER BY rand() LIMIT 1);
                IF count($beneficiary_candidates_normal_recs) > 0 THEN {
                    LET $beneficiary_normal_rec = $beneficiary_candidates_normal_recs[0];
                    LET $normal_amount = rand::float($default_tx_min_amount * 0.1, math::min($default_tx_max_amount * 0.5, $originator_rec.balance * 0.05));
                    IF $normal_amount > 1.0 THEN {
                         CALL fn::create_normal_transaction(
                            $originator_rec.id,
                            $beneficiary_normal_rec.id,
                            $normal_amount,
                            $current_step,
                            $TRANSFER_TX_TYPE // Using the defined LET variable for type
                        );
                    }
                }
            }
        }
    };
};
PRINT "Simulation finished after ", $total_simulation_steps, " steps.";
*/