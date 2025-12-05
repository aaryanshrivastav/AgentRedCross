# ehr_agent.py
from typing import Dict, Any, Optional
from datetime import datetime
from psycopg2.extras import RealDictCursor
from agents.base_agent import BaseAgent
from database.db_pool import PostgresPool


class EHRAgent(BaseAgent):
    """
    PostgreSQL-based EHR agent.
    Handles:
    - create_patient
    - retrieve_patient
    - update_medical_record
    """

    def __init__(self, agent_id: str):
        super().__init__(
            agent_id=agent_id,
            role="ehr_system",
            permissions=[
                "read_all_patient_data",
                "write_all_patient_data",
                "query_across_departments",
                "aggregate_records"
            ]
        )

    # -------------------------------------------------------------------------
    # MESSAGE ROUTER
    # -------------------------------------------------------------------------
    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        action = message.get("action")
        data = message.get("data", {})

        if action == "create_patient":
            return self._create_patient(data)

        elif action == "retrieve_patient":
            return self._retrieve_patient(message["from"], data.get("patient_id"))

        elif action == "update_medical_record":
            return self._update_medical_record(message["from"], data)

        elif action == "update_appointment":
            return self._update_appointment(data)

        return {"status": "error", "message": f"Unknown action: {action}"}

    # -------------------------------------------------------------------------
    # CREATE PATIENT
    # -------------------------------------------------------------------------
    def _create_patient(self, data: Dict[str, Any]) -> Dict[str, Any]:

        if not self.check_permission("write_all_patient_data"):
            return {"status": "denied", "reason": "Permission denied"}

        conn = PostgresPool.get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            INSERT INTO patients (name, dob, contact)
            VALUES (%s, %s, %s)
            RETURNING patient_id;
        """, (data["name"], data["dob"], data["contact"]))

        patient_id = cursor.fetchone()["patient_id"]

        conn.commit()
        PostgresPool.return_conn(conn)

        # Log patient creation
        self.audit_log(
            action="create_patient",
            patient_id=str(patient_id),
            details="New PostgreSQL patient record created."
        )

        return {"status": "success", "patient_id": str(patient_id)}

    # -------------------------------------------------------------------------
    # RETRIEVE PATIENT
    # -------------------------------------------------------------------------
    def _retrieve_patient(self, requester: str, patient_id: str) -> Dict[str, Any]:

        conn = PostgresPool.get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT * FROM patients WHERE patient_id = %s", (patient_id,))
        patient = cursor.fetchone()

        cursor.execute("SELECT * FROM medical_records WHERE patient_id = %s", (patient_id,))
        record = cursor.fetchone()

        PostgresPool.return_conn(conn)

        if not patient:
            return {"status": "error", "message": "Patient not found"}

        # Audit retrieval
        self.audit_log(
            action="retrieve_patient",
            patient_id=patient_id,
            details=f"Requested by {requester}"
        )

        return {
            "status": "success",
            "patient": patient,
            "medical_record": record,
            "retrieval_time_ms": 1
        }

    # -------------------------------------------------------------------------
    # UPDATE MEDICAL RECORD
    # -------------------------------------------------------------------------
    def _update_medical_record(self, requester: str, data: Dict[str, Any]) -> Dict[str, Any]:

        if not self.check_permission("write_all_patient_data"):
            return {"status": "denied"}

        conn = PostgresPool.get_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            INSERT INTO medical_records 
                (patient_id, diagnosis, medications, lab_results, imaging_results)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING record_id;
        """, (
            data["patient_id"],
            data.get("diagnosis"),
            data.get("medications"),
            data.get("lab_results"),
            data.get("imaging_results")
        ))

        record_id = cursor.fetchone()["record_id"]

        conn.commit()
        PostgresPool.return_conn(conn)

        self.audit_log(
            action="update_medical_record",
            patient_id=data["patient_id"],
            details=f"Updated by {requester}"
        )

        return {"status": "success", "record_id": str(record_id)}

    # -------------------------------------------------------------------------
    # UPDATE APPOINTMENT
    # -------------------------------------------------------------------------
    def _update_appointment(self, data: Dict[str, Any]):
        """Stores next-available doctor appointment time."""

        conn = PostgresPool.get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE patients
            SET created_at = created_at  -- no change; placeholder for actual schedule table
            WHERE patient_id = %s
        """, (data["patient_id"],))

        conn.commit()
        PostgresPool.return_conn(conn)

        return {"status": "success", "appointment_time": data["appointment_time"]}
