/**
 * Medical Records Management System
 * Dr. Diana Sánchez - Professional Medical Records
 */

class MedicalRecordsManager {
    constructor() {
        this.visitId = null;
        this.visitData = null;
        this.medications = [];
        this.symptoms = [];
        this.init();
    }

    async init() {
        // Get visit ID from URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const bookingId = urlParams.get('booking_id');
        
        if (!bookingId) {
            alert('Invalid booking ID');
            window.close();
            return;
        }

        try {
            await this.loadOrCreateVisit(bookingId);
            await this.loadVisitData();
            this.setupEventListeners();
        } catch (error) {
            console.error('Initialization error:', error);
            alert('Error loading medical records: ' + error.message);
        }
    }

    async loadOrCreateVisit(bookingId) {
        try {
            // First try to create a visit from the booking
            const response = await fetch('/api/admin/visits', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ booking_id: bookingId })
            });

            const result = await response.json();
            
            if (response.ok) {
                this.visitId = result.visit_id;
            } else {
                // If DB permissions prevent visits creation, fall back to a local draft
                if (result && typeof result.error === 'string' && result.error.toLowerCase().includes('permission denied')) {
                    console.warn('Visit creation failed due to DB permissions, creating draft instead');
                    const draft = await fetch('/api/admin/visits/draft', {
                        method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ booking_id: bookingId })
                    }).then(r=>r.json());
                    if (draft && draft.visit_id) {
                        this.visitId = draft.visit_id;
                        return;
                    }
                }
                throw new Error(result.error || 'Failed to create visit');
            }
        } catch (error) {
            console.error('Error creating visit:', error);
            // Rethrow so init() shows the user an error if even draft creation fails
            throw error;
        }
    }

    async loadVisitData() {
        if (!this.visitId) return;

        try {
            const response = await fetch(`/api/admin/visits/${this.visitId}`);
            const data = await response.json();

            if (response.ok) {
                this.visitData = data.visit;
                this.medications = data.medications || [];
                this.symptoms = data.symptoms || [];
                
                this.populatePatientInfo();
                this.populateVisitData();
                this.renderMedications();
                this.renderSymptoms();
                this.loadPatientHistory(data.patient_history);
            } else {
                throw new Error(data.error || 'Failed to load visit data');
            }
        } catch (error) {
            console.error('Error loading visit data:', error);
            alert('Error loading visit data: ' + error.message);
        }
    }

    populatePatientInfo() {
        if (!this.visitData) return;

        document.getElementById('patient-name').textContent = this.visitData.patient_name || 'N/A';
        document.getElementById('patient-email').textContent = this.visitData.patient_email || 'N/A';
        document.getElementById('patient-phone').textContent = this.visitData.patient_phone || 'N/A';
        document.getElementById('service-type').textContent = this.visitData.service || 'General Consultation';
        
        const visitDate = this.visitData.visit_date || 'N/A';
        const visitTime = this.visitData.visit_time || 'N/A';
        document.getElementById('visit-datetime').textContent = `${visitDate} at ${visitTime}`;
    }

    populateVisitData() {
        if (!this.visitData) return;

        document.getElementById('chief-complaint').value = this.visitData.chief_complaint || '';
        document.getElementById('physical-examination').value = this.visitData.physical_examination || '';
        document.getElementById('diagnosis').value = this.visitData.diagnosis || '';
        document.getElementById('treatment-plan').value = this.visitData.treatment_plan || '';
        document.getElementById('follow-up-instructions').value = this.visitData.follow_up_instructions || '';
        document.getElementById('doctor-notes').value = this.visitData.doctor_notes || '';
        
        if (this.visitData.next_appointment) {
            document.getElementById('next-appointment').value = this.visitData.next_appointment;
        }
    }

    loadPatientHistory(historyData) {
        const aiContent = document.getElementById('ai-history-content');
        const previousVisits = document.getElementById('previous-visits');

        if (historyData && historyData.ai_summary) {
            aiContent.textContent = historyData.ai_summary;
        } else if (this.visitData && this.visitData.ai_history) {
            aiContent.textContent = this.visitData.ai_history;
        } else {
            aiContent.innerHTML = `
                <p>AI Analysis will be generated for this patient based on:</p>
                <ul style="margin-left: 1.5rem; margin-top: 1rem; line-height: 1.6;">
                    <li>Previous visit patterns</li>
                    <li>Symptom correlations</li>
                    <li>Treatment effectiveness</li>
                    <li>Risk factor assessment</li>
                </ul>
                <p style="margin-top: 1rem; font-style: italic; color: var(--text-muted);">
                    AI analysis will be updated daily for comprehensive patient insights.
                </p>
            `;
        }

        if (historyData && historyData.total_visits > 0) {
            previousVisits.innerHTML = `
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                    <div class="detail-item">
                        <span class="detail-label">Total Visits</span>
                        <span class="detail-value">${historyData.total_visits}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Last Visit</span>
                        <span class="detail-value">${historyData.last_visit_date || 'N/A'}</span>
                    </div>
                </div>
                ${historyData.chronic_conditions ? `
                    <div style="margin-top: 1rem;">
                        <strong style="color: var(--warning);">Chronic Conditions:</strong>
                        <p style="margin-top: 0.5rem;">${historyData.chronic_conditions.join(', ')}</p>
                    </div>
                ` : ''}
                ${historyData.allergies ? `
                    <div style="margin-top: 1rem;">
                        <strong style="color: var(--error);">Allergies:</strong>
                        <p style="margin-top: 0.5rem;">${historyData.allergies.join(', ')}</p>
                    </div>
                ` : ''}
            `;
        } else {
            previousVisits.innerHTML = `
                <p style="color: var(--text-muted); text-align: center; padding: 2rem;">
                    This is the patient's first visit. Medical history will be built over time.
                </p>
            `;
        }
    }

    renderMedications() {
        const container = document.getElementById('medication-list');
        container.innerHTML = '';

        this.medications.forEach((med, index) => {
            const medElement = document.createElement('div');
            medElement.className = 'medication-item';
            medElement.innerHTML = `
                <div class="item-header">
                    <span class="item-name">${med.medication_name}</span>
                    <button type="button" onclick="medicalRecords.removeMedication(${index})" 
                            style="background: var(--error); color: white; border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer;">×</button>
                </div>
                <div class="item-details">
                    <strong>Dosage:</strong> ${med.dosage} | 
                    <strong>Frequency:</strong> ${med.frequency} | 
                    <strong>Duration:</strong> ${med.duration || 'As needed'}
                    ${med.instructions ? `<br><strong>Instructions:</strong> ${med.instructions}` : ''}
                </div>
            `;
            container.appendChild(medElement);
        });
    }

    renderSymptoms() {
        const container = document.getElementById('symptom-list');
        container.innerHTML = '';

        this.symptoms.forEach((symptom, index) => {
            const symptomElement = document.createElement('div');
            symptomElement.className = 'symptom-item';
            symptomElement.innerHTML = `
                <div class="item-header">
                    <span class="item-name">${symptom.symptom_name}</span>
                    <button type="button" onclick="medicalRecords.removeSymptom(${index})" 
                            style="background: var(--error); color: white; border: none; border-radius: 50%; width: 24px; height: 24px; cursor: pointer;">×</button>
                </div>
                <div class="item-details">
                    <strong>Severity:</strong> ${symptom.severity}/10 | 
                    <strong>Duration:</strong> ${symptom.duration || 'Not specified'}
                    ${symptom.description ? `<br><strong>Description:</strong> ${symptom.description}` : ''}
                </div>
            `;
            container.appendChild(symptomElement);
        });
    }

    setupEventListeners() {
        // Auto-save functionality
        const formElements = document.querySelectorAll('#medical-form input, #medical-form textarea');
        formElements.forEach(element => {
            element.addEventListener('blur', () => this.autoSave());
        });
    }

    async autoSave() {
        // Auto-save every time a field loses focus
        await this.saveProgress(false); // Silent save
    }

    async saveProgress(showConfirmation = true) {
        if (!this.visitId) return;

        const visitData = {
            chief_complaint: document.getElementById('chief-complaint').value,
            physical_examination: document.getElementById('physical-examination').value,
            diagnosis: document.getElementById('diagnosis').value,
            treatment_plan: document.getElementById('treatment-plan').value,
            follow_up_instructions: document.getElementById('follow-up-instructions').value,
            doctor_notes: document.getElementById('doctor-notes').value,
            next_appointment: document.getElementById('next-appointment').value || null,
            visit_status: 'in_progress'
        };

        // Include current medications and symptoms so the server has a full snapshot
        try {
            visitData.medications_prescribed = this.medications.map(m => ({
                medication_name: m.medication_name,
                dosage: m.dosage,
                frequency: m.frequency,
                duration: m.duration || null,
                instructions: m.instructions || null,
                id: m.id || null
            }));
        } catch (e) { visitData.medications_prescribed = []; }

        try {
            visitData.symptoms = this.symptoms.map(s => ({
                symptom_name: s.symptom_name,
                severity: s.severity || null,
                duration: s.duration || null,
                description: s.description || null,
                id: s.id || null
            }));
        } catch (e) { visitData.symptoms = []; }

        try {
            // Add admin token header if available (TOK defined in admin UI)
            const headers = { 'Content-Type': 'application/json' };
            
            // Try to get admin token from cookie
            const adminToken = document.cookie.match(/dds_admin=([^;]+)/);
            if (adminToken && adminToken[1]) {
                headers['X-Admin-Token'] = adminToken[1];
            } else {
                console.warn('No admin token found in cookies');
            }

            // Disable Save button while saving
            const saveBtn = document.querySelector('.btn-secondary[onclick="saveProgress()"]');
            if (saveBtn) { saveBtn.disabled = true; saveBtn.textContent = 'Saving…'; }

            // If this is a draft visit id, use the draft update endpoint
            let response;
            if (String(this.visitId).startsWith('draft-')) {
                response = await fetch(`/api/admin/visits/draft/${this.visitId}`, {
                    method: 'PUT', headers, body: JSON.stringify(visitData)
                });
            } else {
                response = await fetch(`/api/admin/visits/${this.visitId}`, {
                    method: 'PUT', headers, body: JSON.stringify(visitData)
                });
            }

            const result = await response.json();

            if (response.ok && showConfirmation) {
                this.showNotification('Progress saved successfully', 'success');
            } else if (!response.ok) {
                console.error('Save failed:', result);
                throw new Error(result.error || `Failed to save progress (Status: ${response.status})`);
            }
            if (saveBtn) { saveBtn.disabled = false; saveBtn.textContent = 'Save Progress'; }
        } catch (error) {
            console.error('Error saving progress:', error);
            if (showConfirmation) {
                this.showNotification('Error saving progress: ' + error.message, 'error');
            }
            const saveBtn = document.querySelector('.btn-secondary[onclick="saveProgress()"]');
            if (saveBtn) { saveBtn.disabled = false; saveBtn.textContent = 'Save Progress'; }
            // Re-throw so caller knows save failed
            throw error;
        }
    }

    async submitVisit() {
        // First save all current progress
        try {
            await this.saveProgress(false);
        } catch (error) {
            this.showNotification('Failed to save progress before completing visit', 'error');
            return;
        }

        if (!this.validateForm()) {
            this.showNotification('Please fill in all required fields', 'error');
            return;
        }

        try {
            // Get admin token from cookie
            const adminToken = document.cookie.match(/dds_admin=([^;]+)/);
            const headers = { 'Content-Type': 'application/json' };
            if (adminToken && adminToken[1]) {
                headers['X-Admin-Token'] = adminToken[1];
            }

            const response = await fetch(`/api/admin/visits/${this.visitId}/complete`, {
                method: 'POST',
                headers: headers
            });

            const result = await response.json();

            if (response.ok) {
                this.showNotification('Visit completed successfully! Summary email sent.', 'success');
                setTimeout(() => {
                    window.close();
                }, 2000);
            } else {
                console.error('Complete visit failed:', result);
                throw new Error(result.error || `Failed to complete visit (Status: ${response.status})`);
            }
        } catch (error) {
            console.error('Error completing visit:', error);
            this.showNotification('Error completing visit: ' + error.message, 'error');
        }
    }

    validateForm() {
        const requiredFields = [
            'chief-complaint',
            'diagnosis',
            'treatment-plan'
        ];

        for (const fieldId of requiredFields) {
            const field = document.getElementById(fieldId);
            if (!field.value.trim()) {
                field.focus();
                return false;
            }
        }

        return true;
    }

    async addMedication() {
        document.getElementById('medication-modal').style.display = 'block';
    }

    async addSymptom() {
        document.getElementById('symptom-modal').style.display = 'block';
    }

    async saveMedication() {
        const medData = {
            medication_name: document.getElementById('med-name').value,
            dosage: document.getElementById('med-dosage').value,
            frequency: document.getElementById('med-frequency').value,
            duration: document.getElementById('med-duration').value,
            instructions: document.getElementById('med-instructions').value
        };

        if (!medData.medication_name || !medData.dosage || !medData.frequency) {
            this.showNotification('Please fill in medication name, dosage, and frequency', 'error');
            return;
        }

        try {
            const response = await fetch(`/api/admin/visits/${this.visitId}/medications`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(medData)
            });

            const result = await response.json();

            if (response.ok) {
                // Add to local array and re-render
                this.medications.push({ ...medData, id: result.medication_id });
                this.renderMedications();
                this.closeMedicationModal();
                this.showNotification('Medication added successfully', 'success');
            } else {
                throw new Error(result.error || 'Failed to add medication');
            }
        } catch (error) {
            console.error('Error adding medication:', error);
            this.showNotification('Error adding medication: ' + error.message, 'error');
        }
    }

    async saveSymptom() {
        const symptomData = {
            symptom_name: document.getElementById('symptom-name').value,
            severity: parseInt(document.getElementById('symptom-severity').value),
            duration: document.getElementById('symptom-duration').value,
            description: document.getElementById('symptom-description').value
        };

        if (!symptomData.symptom_name) {
            this.showNotification('Please enter symptom name', 'error');
            return;
        }

        try {
            const response = await fetch(`/api/admin/visits/${this.visitId}/symptoms`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(symptomData)
            });

            const result = await response.json();

            if (response.ok) {
                // Add to local array and re-render
                this.symptoms.push({ ...symptomData, id: result.symptom_id });
                this.renderSymptoms();
                this.closeSymptomModal();
                this.showNotification('Symptom added successfully', 'success');
            } else {
                throw new Error(result.error || 'Failed to add symptom');
            }
        } catch (error) {
            console.error('Error adding symptom:', error);
            this.showNotification('Error adding symptom: ' + error.message, 'error');
        }
    }

    removeMedication(index) {
        if (confirm('Are you sure you want to remove this medication?')) {
            this.medications.splice(index, 1);
            this.renderMedications();
            this.showNotification('Medication removed', 'success');
        }
    }

    removeSymptom(index) {
        if (confirm('Are you sure you want to remove this symptom?')) {
            this.symptoms.splice(index, 1);
            this.renderSymptoms();
            this.showNotification('Symptom removed', 'success');
        }
    }

    closeMedicationModal() {
        document.getElementById('medication-modal').style.display = 'none';
        // Clear form
        document.getElementById('med-name').value = '';
        document.getElementById('med-dosage').value = '';
        document.getElementById('med-frequency').value = '';
        document.getElementById('med-duration').value = '';
        document.getElementById('med-instructions').value = '';
    }

    closeSymptomModal() {
        document.getElementById('symptom-modal').style.display = 'none';
        // Clear form
        document.getElementById('symptom-name').value = '';
        document.getElementById('symptom-severity').value = '5';
        document.getElementById('symptom-duration').value = '';
        document.getElementById('symptom-description').value = '';
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? 'var(--success)' : type === 'error' ? 'var(--error)' : 'var(--accent)'};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            z-index: 10000;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease;
        `;
        notification.textContent = message;

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(0)';
        }, 10);

        // Remove after 4 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 4000);
    }
}

// Global functions for HTML onclick events
function closeWindow() {
    if (confirm('Are you sure you want to close? Any unsaved changes will be lost.')) {
        window.close();
    }
}

function addSymptom() {
    medicalRecords.addSymptom();
}

function addMedication() {
    medicalRecords.addMedication();
}

function saveSymptom() {
    medicalRecords.saveSymptom();
}

function saveMedication() {
    medicalRecords.saveMedication();
}

function closeSymptomModal() {
    medicalRecords.closeSymptomModal();
}

function closeMedicationModal() {
    medicalRecords.closeMedicationModal();
}

function saveProgress() {
    medicalRecords.saveProgress();
}

function submitVisit() {
    medicalRecords.submitVisit();
}

// Initialize the medical records manager
let medicalRecords;
document.addEventListener('DOMContentLoaded', () => {
    medicalRecords = new MedicalRecordsManager();
});

// Handle modal clicks
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.style.display = 'none';
    }
});