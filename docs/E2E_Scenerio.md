Automation Requirements Artifact: MVA 56416032
Step 1: Dashboard Audit
Logic: The script scans the "Work Items" tab to ensure the task isn't already "Open."

Target HTML Class: fleet-operations-pwa__status-red

Action: If no "Open" card for the target task exists, click + Add Work Item.

[Insert Image 1: Main Dashboard with "+ Add Work Item" button]

Step 2: Complaint Selection
Logic: Identify if the vehicle already has a recorded complaint that can be converted into a Work Item.

Target Text: "Glass Damage - Windshield Crack" or "PM"

Action: Click the matching complaint block; if empty, click Add New Complaint.

[Insert Image 2: "Open Complaint(s)" selection screen]

Step 3: Creating New Complaint (Sub-Wizard)
Logic: If no complaint was found in Step 2, the script follows this hardcoded safety and categorization path.

Drivability: Click the Yes checkmark icon.

Categorization: Select the icon matching the intent (Oil Can for PM / Cracked Window for Glass).

Submission: Click Submit Complaint.

[Insert Image 3: Category Icons Grid (PM/Glass/Keys)]
[Insert Image 4: "Submit Complaint" confirmation screen]

Step 4: Mileage & Service Assignment
Logic: Bridge the complaint to a billable service record.

Mileage: Confirm the value in the RECORDED MILEAGE input field (e.g., 37010) and click Next.

OpCode: Search for and select the specific Corrective Action (e.g., "PM Gas" or "Glass Calibrate").

Creation: Click Create Work Item.

[Insert Image 5: Mileage Entry Screen (37010)]
[Insert Image 6: Corrective Action List showing "PM Gas" selected]

Step 5: Completion Handshake
Logic: Finalize the transaction and return to the asset view.

Action: Click Done.

Validation: Verify the dashboard now displays a new Open card in the list.

[Insert Image 7: Final "Done" button screen]
[Insert Image 8: Final Dashboard showing the new Open PM Gas card]