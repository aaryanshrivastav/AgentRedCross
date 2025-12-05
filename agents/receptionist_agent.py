# receptionist_agent.py
from typing import Dict, Any
from datetime import datetime
from agents.base_agent import BaseAgent


class ReceptionistAgent(BaseAgent):
    """
    Handles patient intake:
    - Registers patient (via EHR Agent)
    - Schedules doctor
    - Logs events
    """

    def __init__(self, agent_id: str):
        super().__init__(
            agent_id=agent_id,
            role="receptionist",
            permissions=[
                "create_patient",
                "read_patient_basics",
                "update_appointment",
                "schedule_doctor"
            ]
        )

    # -------------------------------------------------------------------------
    # MESSAGE ROUTER
    # -------------------------------------------------------------------------
    def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        action = message.get("action")

        if action == "patient_intake":
            return self.handle_patient_intake(message["data"])

        return {"status": "error", "message": f"Unknown action {action}"}

    # -------------------------------------------------------------------------
    # PATIENT INTAKE WORKFLOW
    # -------------------------------------------------------------------------
    def handle_patient_intake(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:

        # 1. Validate permission
        if not self.check_permission("create_patient"):
            return {"status": "denied", "reason": "Permission denied"}

        # 2. Ask EHR Agent to create the patient
        self.send_message(
            target_agent="ehr_agent",
            action="create_patient",
            data=patient_data
        )

        # Patient ID is added by EHR Agent, orchestrator returns result
        patient_id = patient_data.get("patient_id", "PENDING")

        # 3. Audit creation
        self.audit_log(
            action="patient_registered",
            patient_id=patient_id,
            details="Receptionist registered new patient."
        )

        # 4. Schedule doctor
        if self.check_permission("schedule_doctor"):
            self.send_message(
                target_agent="doctor_scheduler",
                action="schedule_next_available",
                data={"patient_id": patient_id}
            )

        # 5. Update appointment in EHR
        self.send_message(
            target_agent="ehr_agent",
            action="update_appointment",
            data={
                "patient_id": patient_id,
                "appointment_time": datetime.now().isoformat()
            }
        )

        # Audit appointment
        self.audit_log(
            action="doctor_scheduled",
            patient_id=patient_id,
            details="Appointment scheduled within 15 minutes."
        )

        return {
            "status": "success",
            "message": "Patient registered and routed to doctor",
            "patient_id": patient_id
        }
