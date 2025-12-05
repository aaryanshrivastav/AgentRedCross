-- hospital_schema.sql

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

---------------------------------------------------------
-- PATIENTS TABLE
---------------------------------------------------------
CREATE TABLE IF NOT EXISTS patients (
    patient_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    dob DATE NOT NULL,
    contact TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(name);


---------------------------------------------------------
-- MEDICAL RECORDS TABLE
---------------------------------------------------------
CREATE TABLE IF NOT EXISTS medical_records (
    record_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(patient_id) ON DELETE CASCADE,
    diagnosis TEXT,
    medications TEXT,
    lab_results JSONB,
    imaging_results JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_medical_records_patient ON medical_records(patient_id);


---------------------------------------------------------
-- ACCESS LOGS
---------------------------------------------------------
CREATE TABLE IF NOT EXISTS access_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id TEXT NOT NULL,
    patient_id UUID,
    action TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_access_logs_patient ON access_logs(patient_id);
CREATE INDEX IF NOT EXISTS idx_access_logs_agent ON access_logs(agent_id);


---------------------------------------------------------
-- OPTIONAL: LAB REQUESTS TABLE
---------------------------------------------------------
CREATE TABLE IF NOT EXISTS lab_requests (
    request_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES patients(patient_id),
    doctor_id TEXT,
    test_type TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
