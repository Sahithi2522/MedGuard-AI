(() => {
  const extraNavigation = {
    patient: [
      ['profile', 'Health profile', 'heart'],
      ['prescriptions', 'Prescription review', 'file'],
      ['simulator', 'What-if simulator', 'scan'],
      ['network', 'Interaction network', 'grid'],
      ['timeline', 'History comparison', 'clock'],
      ['evidence', 'Evidence status', 'shield'],
      ['assistant', 'MedGuard Assistant', 'heart'],
      ['appointments', 'Appointments', 'calendar'],
      ['caregiver', 'Care sharing', 'users'],
      ['capabilities', 'Feature coverage', 'check']
    ],
    doctor: [
      ['network', 'Interaction network', 'grid'],
      ['evidence', 'Evidence status', 'shield'],
      ['appointments', 'Appointments', 'calendar'],
      ['assistant', 'MedGuard Assistant', 'heart'],
      ['capabilities', 'Feature coverage', 'check']
    ],
    pharmacist: [
      ['patients', 'Patients', 'heart'],
      ['network', 'Interaction network', 'grid'],
      ['evidence', 'Evidence status', 'shield'],
      ['appointments', 'Appointments', 'calendar'],
      ['assistant', 'MedGuard Assistant', 'heart'],
      ['capabilities', 'Feature coverage', 'check']
    ],
    admin: [
      ['analytics', 'Aggregate analytics', 'grid'],
      ['audit', 'Audit events', 'file'],
      ['evidence', 'Reference status', 'shield'],
      ['capabilities', 'Feature coverage', 'check']
    ],
    caregiver: [
      ['dependents', 'Authorized dependents', 'users'],
      ['notifications', 'Notifications', 'bell'],
      ['assistant', 'MedGuard Assistant', 'heart'],
      ['capabilities', 'Feature coverage', 'check']
    ]
  };

  Object.entries(extraNavigation).forEach(([role, links]) => {
    links.forEach(link => {
      if (!navByRole[role].some(existing => existing[0] === link[0])) navByRole[role].push(link);
    });
  });

  const catalog = [
    ['Drug-drug interaction detection', 'Limited', 'No verified interaction reference is configured; the checker returns unable to verify.'],
    ['Drug-disease interaction detection', 'Limited', 'Patient-entered conditions are stored; validated disease rules are unavailable.'],
    ['Duplicate medication detection', 'Demo check', 'Exact ingredient-text duplicates are detected; product equivalence is not inferred.'],
    ['Dosage screening', 'Limited', 'Missing dose/frequency is flagged; clinical dose limits are not configured.'],
    ['Allergy conflict detection', 'Limited', 'Exact text matches are flagged for professional confirmation; cross-reactivity is not assessed.'],
    ['Explainable safety alerts', 'Demo check', 'Findings include affected entries, explanation, source status, uncertainty, and next step.'],
    ['Prescription OCR and NLP', 'Manual fallback', 'PDF/JPEG/PNG upload and manual confirmation work; OCR/NLP is not configured.'],
    ['AI medication assistant', 'Fixed FAQ', 'A bounded safety FAQ is available; no LLM or clinical retrieval source is configured.'],
    ['What-if medication simulator', 'Demo check', 'A proposed entry can be screened against the patient-owned medication list.'],
    ['Interaction network visualization', 'Demo check', 'The graph uses actual check nodes and exact-duplicate edges; no interaction edges are invented.'],
    ['Medication history comparison', 'Demo check', 'Saved screening snapshots can be compared; full start/stop history is not modeled.'],
    ['Evidence and uncertainty viewer', 'Source status', 'Alert uncertainty is shown; the evidence library reports that no source is configured.'],
    ['Patient dashboard', 'Available', 'Patient dashboard and patient-owned records are available.'],
    ['Doctor dashboard', 'Available', 'Linked patient medication records and a scoped synthetic prescription workflow are available for active doctor reviews.'],
    ['Pharmacist dashboard', 'Available', 'Linked patient medication records are available for patients who requested pharmacist review.'],
    ['Admin dashboard', 'Available', 'Admin-only account view, aggregate counts, and audit events are available.'],
    ['Caregiver access', 'Scoped demo', 'Patient-granted permissions expose only the selected medication, schedule, or report scope.'],
    ['Appointment and review workflow', 'Simulated', 'Requests persist and can be updated; no real professional availability is connected.'],
    ['Secure authentication', 'Available', 'Salted password hashes, random server sessions, HttpOnly/SameSite cookies, and expiry.'],
    ['Role-based access control', 'Available', 'Backend routes enforce roles; public sign-up cannot self-assign professional roles.'],
    ['Database persistence', 'Available', 'SQLite stores demo records, reviews, checks, schedules, and audit metadata.'],
    ['REST API integration', 'Available', 'Same-origin authenticated JSON API backs the workflows.'],
    ['Safety report generation', 'Demo summary', 'Saved analysis summaries are viewable and exportable; they are not clinical recommendations.'],
    ['Medication reminders and notifications', 'Local only', 'Reminder preferences and in-app events persist; timed delivery/email/SMS are unavailable.'],
    ['English and Telugu support', 'Partial', 'A bilingual feature glossary is shown; full Telugu interface translation is not complete.'],
    ['Clinical evidence library', 'Unavailable', 'No licensed source or clinical reference records are bundled.'],
    ['Audit logs', 'Available', 'Sensitive demo actions are recorded; admin access is aggregate/metadata-only.'],
    ['Analytics dashboard', 'Available', 'Admin receives aggregate counts without patient-level details.'],
    ['PDF and data export', 'Browser export', 'JSON/CSV download and browser print-to-PDF are available for saved summaries.'],
    ['Responsive mobile interface', 'Available', 'Mobile dashboard, bottom navigation, and mobile sign-out are implemented.']
  ];

  const featureStyles = document.createElement('style');
  featureStyles.textContent = `
    .feature-toolbar{display:flex;gap:9px;flex-wrap:wrap;margin:12px 0}
    .feature-form{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;margin:12px 0}
    .feature-form input,.feature-form select,.feature-form textarea{width:100%;min-width:0;min-height:40px;padding:9px 11px;border:1px solid #d5e3e2;background:rgba(255,255,255,.84);border-radius:10px;color:#15313d}
    .feature-form textarea{min-height:90px;grid-column:1/-1}
    .feature-form button{grid-column:1/-1;justify-self:start}
    .feature-status{display:inline-block;padding:4px 7px;border-radius:20px;background:#e6f4ed;color:#28704f;font-size:9px;font-weight:750;white-space:nowrap}
    .feature-status.limited{background:#fff3df;color:#8a5b1b}
    .feature-grid-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}
    .feature-item{padding:13px;border:1px solid rgba(29,78,84,.1);border-radius:12px;background:rgba(255,255,255,.55)}
    .feature-item strong{display:block;font-size:11px;margin-bottom:6px}
    .feature-item p{margin:0;color:#69808a;font-size:10px;line-height:1.5}
    .network-list{display:flex;gap:9px;flex-wrap:wrap;margin:14px 0}
    .network-node{border:1px solid #b9d8d0;border-radius:13px;background:#eaf6f1;padding:11px 14px;font-size:11px}
    .network-edge{width:100%;font-size:10px;color:#8a5b1b;padding:6px 9px;border-left:2px solid #c79134}
    .language-note{font-size:11px;line-height:1.6;color:#607880}
    .hidden-file{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
    .document-preview{width:min(900px,calc(100vw - 28px));height:min(88vh,900px);max-width:none;max-height:none;padding:14px;border:1px solid rgba(255,255,255,.9);border-radius:16px;background:#f4faf8;color:#15313d;box-shadow:0 24px 80px rgba(21,49,61,.28)}
    .document-preview::backdrop{background:rgba(21,49,61,.46);backdrop-filter:blur(5px)}
    .document-preview__close{display:flex;justify-content:flex-end;margin-bottom:10px}
    .document-preview iframe,.document-preview img{width:100%;height:calc(100% - 48px);border:0;border-radius:10px;background:white;object-fit:contain}
    @media(max-width:680px){.feature-grid-list,.feature-form{grid-template-columns:1fr}.feature-form button{grid-column:auto}}
    @media print{.sidebar,.app-top,.mobile-bottom,.feature-toolbar,button{display:none!important}.app-shell{display:block}.main{padding:0}.content{max-width:none}.glass{box-shadow:none;background:white}}
  `;
  document.head.append(featureStyles);

  const escHtml = value => esc(value ?? '');
  const panel = (title, body, extra = '') => `<section class="panel glass"><div class="panel-head"><h2>${title}</h2>${extra}</div>${body}</section>`;
  const empty = (title, detail) => `<div class="empty"><b>${title}</b>${detail}</div>`;
  const entryList = entries => entries.length ? `<div style="overflow:auto"><table class="table"><thead><tr><th>Name</th><th>Details</th><th>Source</th></tr></thead><tbody>${entries.map(entry => `<tr><td>${escHtml(entry.name || entry.ingredient)}</td><td>${escHtml(entry.reaction || entry.severity || entry.strength || entry.schedule || '')}</td><td>${escHtml(entry.source || 'Patient-entered')}</td></tr>`).join('')}</tbody></table></div>` : empty('No records yet', 'Add a record below. It will be labeled patient-entered, not clinically verified.');
  const resultMarkup = result => {
    const alerts = result.alerts || [];
    return `<div class="results">${alerts.length ? alerts.map(alert => `<article class="result-item"><strong>${escHtml(alert.category)} · ${escHtml(alert.severity)}</strong><b>Affected:</b> ${escHtml((alert.medicines || []).join(', ') || 'Medication list')}<br>${escHtml(alert.explanation)}<br><span class="disclaimer-small">Evidence: ${escHtml(alert.evidence_source)} · ${escHtml(alert.verification_status)}. ${escHtml(alert.uncertainty)}<br>Next step: ${escHtml(alert.next_step)}</span></article>`).join('') : empty('No records supplied', 'Add confirmed entries before running a screening.')}</div><p class="disclaimer-small">${escHtml(result.disclaimer || 'Screening summary only; not clinical advice.')}</p>`;
  };
  const download = (filename, content, type) => {
    const url = URL.createObjectURL(new Blob([content], { type }));
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
  };
  const readBase64 = file => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(',')[1] || '');
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });

  function modulePage(view, role, data) {
    if (view === 'patients' && ['doctor', 'pharmacist'].includes(role)) return `${panel('Linked patient records', `<p class="disclaimer-small">Only patients who requested a ${escHtml(role)} review appear here. Medication records are stored on the patient account.</p><div id="linked-patient-records">Loading linked records…</div>`)}${role === 'doctor' ? panel('Record a doctor-entered medicine', '<p class="disclaimer-small">Synthetic demo workflow only. Confirm any real prescription and instructions with a qualified healthcare professional.</p><form id="provider-medication-form" class="feature-form"><select name="patient_id" id="linked-patient-select" required><option value="">Choose a linked patient</option></select><input name="name" placeholder="Medicine name" required maxlength="120"><input name="ingredient" placeholder="Active ingredient" required maxlength="120"><input name="strength" placeholder="Strength"><input name="dose" placeholder="Dose as documented"><input name="frequency" placeholder="Frequency as documented"><input name="route" placeholder="Route"><input name="duration" placeholder="Duration"><input name="schedule" placeholder="Schedule note"><button class="btn btn-primary btn-small">Add to patient medication list</button></form><div id="provider-medication-status" aria-live="polite"></div>') : ''}`;
    if (view === 'profile' && role === 'patient') return `${panel('Health profile', '<div id="profile-records">Loading profile…</div>')}<div class="dashboard-grid"><form class="panel glass feature-form" id="allergy-form"><h2>Record an allergy</h2><input name="ingredient" placeholder="Substance / ingredient" required maxlength="120"><input name="reaction" placeholder="Recorded reaction (optional)" maxlength="250"><select name="severity"><option>Unknown</option><option>Mild</option><option>Moderate</option><option>Severe</option></select><button class="btn btn-primary btn-small">Save allergy</button></form><form class="panel glass feature-form" id="condition-form"><h2>Record a condition</h2><input name="name" placeholder="Condition name" required maxlength="120"><button class="btn btn-primary btn-small">Save condition</button></form></div><p class="disclaimer-small">These are user-entered records and are not diagnoses or verified clinical data.</p>`;
    if (view === 'prescriptions' && role === 'patient') return `${panel('Prescription review', '<p class="secondary" style="font-size:12px">Upload PDF, PNG, or JPEG (maximum 5 MB). This demo securely stores the file but has no OCR/NLP engine. Extracted fields must be entered and confirmed manually.</p><form id="upload-form" class="feature-form"><input type="file" name="document" accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg" required><button class="btn btn-primary btn-small">Upload document</button></form><div id="upload-message" class="results"></div><div id="prescription-list">Loading documents…</div>')}${panel('Confirm a manual medication entry', '<p class="disclaimer-small">Only save medicine details you have checked against the original prescription. No text was extracted automatically.</p><form id="manual-confirm-form" class="feature-form"><input name="name" placeholder="Medicine name" required><input name="ingredient" placeholder="Active ingredient" required><input name="strength" placeholder="Strength"><input name="dose" placeholder="Dose as written"><input name="frequency" placeholder="Frequency as written"><input name="route" placeholder="Route as written"><button class="btn btn-primary btn-small">Save confirmed entry</button></form>')}`;
    if (view === 'simulator' && role === 'patient') return `${panel('Preliminary what-if check', '<p class="callout">Simulation only. It does not approve a proposed medicine or assess interactions because verified clinical references are unavailable.</p><form id="simulation-form" class="feature-form"><input name="name" placeholder="Proposed medicine name" required><input name="ingredient" placeholder="Active ingredient, if known"><input name="strength" placeholder="Strength (optional)"><input name="dose" placeholder="Dose as written (optional)"><button class="btn btn-primary btn-small">Compare with saved list</button></form><div id="simulation-results"></div>')}`;
    if (view === 'checker' && ['doctor','pharmacist'].includes(role)) return panel('Manual medication screening', '<p class="disclaimer-small">Enter only synthetic or appropriately authorized data. No patient record is loaded or inferred. Exact duplicate text can be identified; interaction, disease, dose limits, and product equivalence remain unverified.</p><div id="professional-medications"><div class="feature-form professional-medication"><input name="name" placeholder="Medicine name" required><input name="ingredient" placeholder="Active ingredient (if known)"></div><div class="feature-form professional-medication"><input name="name" placeholder="Medicine name" required><input name="ingredient" placeholder="Active ingredient (if known)"></div></div><div class="feature-toolbar"><button class="btn btn-quiet btn-small" id="add-professional-medication" type="button">Add medicine</button><button class="btn btn-primary btn-small" id="run-professional-check" type="button">Run limited check</button></div><div id="professional-results"></div>');
    if (view === 'network') return panel('Analysis network', '<p class="secondary" style="font-size:12px">Nodes and duplicate-text edges are derived from your saved screening results. No interaction edges are fabricated.</p><div id="network-view">Loading saved checks…</div>');
    if (view === 'timeline') return panel('Safety history comparison', '<p class="secondary" style="font-size:12px">Compares saved screening snapshots, not confirmed prescription changes. Patient-entered medication history is incomplete.</p><div id="history-view">Loading saved checks…</div>');
    if (view === 'evidence') return panel('Clinical evidence and uncertainty', '<div id="evidence-view">Checking reference configuration…</div>');
    if (view === 'assistant') return `${panel('MedGuard Assistant', '<p class="disclaimer-small">Fixed, safety-bounded help only. It is not an AI clinician and has no verified drug-reference retrieval.</p><form id="assistant-form" class="feature-form"><textarea name="question" placeholder="Ask about the demo checker or its limits" required maxlength="1000"></textarea><button class="btn btn-primary btn-small">Ask</button></form><div id="assistant-response" aria-live="polite"></div>')}<div class="feature-toolbar">${['What does a duplicate mean?','Can you verify interactions?','I have an allergy question'].map(question => `<button class="btn btn-quiet btn-small" data-chat-prompt="${question}">${question}</button>`).join('')}</div>`;
    if (view === 'appointments') return `${panel('Professional review requests', '<p class="disclaimer-small">Appointments are simulated. No real clinician availability or confirmed appointment is represented.</p><div id="appointment-list">Loading requests…</div>')}<form id="appointment-form" class="panel glass feature-form"><h2>Request a review</h2><select name="professional_role"><option value="doctor">Doctor review</option><option value="pharmacist">Pharmacist review</option></select><input name="requested_for" type="datetime-local" aria-label="Preferred time (demo)"><input name="note" maxlength="500" placeholder="Optional note"><button class="btn btn-primary btn-small">Submit simulated request</button></form>`;
    if (view === 'schedule' && role === 'patient') return `${panel('Medication schedule', '<p class="disclaimer-small">Schedule labels follow the entered instructions. This demo does not change doses or send timed reminders.</p><div id="schedule-list">Loading schedules…</div>')}<form id="schedule-form" class="panel glass feature-form"><h2>Add a schedule label</h2><select name="medication_id" id="schedule-medication" required><option value="">Loading medicines…</option></select><input name="time_label" placeholder="e.g. Morning, as prescribed" required maxlength="80"><label><input type="checkbox" name="reminder_enabled"> Save an in-app reminder preference</label><button class="btn btn-primary btn-small">Save schedule</button></form>`;
    if (view === 'schedule' && role === 'caregiver') return panel('Authorized medication schedules', '<p class="disclaimer-small">Only schedule-scoped permissions are shown. Dose timing is not changed and reminders are not delivered.</p><div id="caregiver-schedules">Loading permitted schedules…</div>');
    if (view === 'caregiver' && role === 'patient') return `${panel('Authorized sharing', '<p class="disclaimer-small">Grant only a specific scope to the caregiver demo account. Permissions are listed below and can be revoked. No access is granted by default.</p><form id="caregiver-grant-form" class="feature-form"><input name="email" type="email" placeholder="caregiver@medguard.demo" required><select name="permission"><option value="medications">Medication summary</option><option value="schedule">Schedule summary</option><option value="reports">Safety report summaries</option></select><button class="btn btn-primary btn-small">Grant selected scope</button></form><div id="caregiver-status"></div><div id="patient-consents"></div>')}`;
    if (view === 'dependents' && role === 'caregiver') return panel('Authorized dependents', '<div id="dependent-list">Loading authorized shares…</div>');
    if (view === 'notifications') return panel('In-app notifications', '<div id="notification-list">Loading notifications…</div><p class="disclaimer-small">No email, SMS, push, or timed dose reminders are delivered by this local demo.</p>');
    if (view === 'reports' && role === 'patient') return panel('Saved safety summaries', '<div class="feature-toolbar"><button class="btn btn-quiet btn-small" id="export-medications-json">Export medication data (JSON)</button><button class="btn btn-quiet btn-small" id="export-medications-csv">Export medication data (CSV)</button><button class="btn btn-quiet btn-small" id="print-reports">Print / Save as PDF</button></div><div id="report-list">Loading saved reports…</div><p class="disclaimer-small">Every summary is an automated screening result, not a treatment recommendation.</p>');
    if (view === 'analytics' && role === 'admin') return panel('De-identified workflow analytics', '<div id="analytics-view">Loading aggregate data…</div>');
    if (view === 'audit' && role === 'admin') return panel('Audit events', '<div id="audit-view">Loading security event metadata…</div>');
    if (view === 'capabilities') return panel('30-feature coverage', `<p class="secondary" style="font-size:12px">All 30 requested areas are mapped below. “Available” means the demo workflow exists; “Limited” and “Unavailable” identify explicit integration gaps. This is not a claim that 30 clinical features are production-ready.</p><div class="feature-grid-list">${catalog.map(([name, status, detail], index) => `<article class="feature-item"><strong>${String(index + 1).padStart(2, '0')}. ${name} <span class="feature-status ${['Limited','Manual fallback','Fixed FAQ','Scoped demo','Simulated','Source status','Unavailable','Partial','Demo check','Demo summary','Local only','Browser export'].includes(status) ? 'limited' : ''}">${status}</span></strong><p>${detail}</p></article>`).join('')}</div><div class="feature-toolbar"><label class="language-note">Feature glossary / பொருள் விளக்கம் <select id="glossary-language"><option value="en">English</option><option value="te">తెలుగు</option></select></label></div><p id="glossary-note" class="language-note">Prototype coverage is explicit; clinical source integrations are not bundled.</p>`);
    if (view === 'analytics' || view === 'audit' || view === 'dependents' || view === 'profile' || view === 'prescriptions' || view === 'simulator' || view === 'caregiver') return panel('Not available for this role', empty('Access restricted', 'This view is limited to its intended workspace role.'));
    return null;
  }

  const originalPageContent = pageContent;
  pageContent = function(view, role, data) {
    return modulePage(view, role, data) || originalPageContent(view, role, data);
  };
  const originalPageDescription = pageDescription;
  pageDescription = function(view, role) {
    return view === 'patients' ? `Linked records for patients who requested a ${role} review.` : originalPageDescription(view, role);
  };

  const originalBindActions = bindActions;
  bindActions = function(view, role, data) {
    originalBindActions(view, role, data);
    if (view === 'home' && role === 'patient') {
      const checkButton = document.querySelector('#app [data-action="check"]');
      const panelElement = checkButton?.closest('.panel');
      if (checkButton && panelElement) {
        const results = document.createElement('div');
        results.id = 'check-results';
        results.className = 'results';
        results.setAttribute('aria-live', 'polite');
        results.setAttribute('aria-atomic', 'true');
        const callout = panelElement.querySelector('.callout');
        panelElement.insertBefore(results, callout || null);

        const activeButton = checkButton.cloneNode(true);
        checkButton.replaceWith(activeButton);
        activeButton.addEventListener('click', async () => {
          activeButton.disabled = true;
          activeButton.textContent = 'Checking…';
          results.innerHTML = '<div class="result-item">Checking the saved medication list…</div>';
          try {
            const result = await api('/api/safety/check', { method: 'POST', body: '{}' });
            results.innerHTML = resultMarkup(result);
          } catch (error) {
            showError(results, error);
          } finally {
            activeButton.disabled = false;
            activeButton.textContent = 'Check list';
          }
        });
      }
    }
    renderModuleData(view, role, data);
  };

  async function renderModuleData(view, role, dashboardData) {
    const byId = id => document.getElementById(id);
    const formData = form => Object.fromEntries(new FormData(form).entries());
    const postForm = async (form, url) => api(url, { method: 'POST', body: JSON.stringify(formData(form)) });
    const showError = (target, error) => { if (target) target.innerHTML = `<div class="result-item">${escHtml(error.message)}</div>`; };
    const fetchProfile = async () => api('/api/profile');

    if (view === 'patients' && ['doctor', 'pharmacist'].includes(role)) {
      const patients = dashboardData.patients || [];
      const medicationRows = patients.flatMap(patient => patient.medications.length ? patient.medications.map(medication => `<tr><td>${escHtml(patient.name)}</td><td>${escHtml(medication.name)}</td><td>${escHtml(medication.strength || 'Not recorded')}</td><td>${escHtml(medication.dose || medication.frequency || medication.schedule || 'Instructions not recorded')}</td><td>${escHtml(medication.source || 'Patient-entered')}${medication.prescriber_name ? `<br><span class="disclaimer-small">${escHtml(medication.prescriber_name)}</span>` : ''}</td></tr>`) : `<tr><td>${escHtml(patient.name)}</td><td colspan="4">No medication records yet</td></tr>`);
      byId('linked-patient-records').innerHTML = medicationRows.length ? `<div style="overflow:auto"><table class="table"><thead><tr><th>Patient</th><th>Medicine</th><th>Strength</th><th>Instructions</th><th>Source / prescriber</th></tr></thead><tbody>${medicationRows.join('')}</tbody></table></div>` : empty('No linked patient records', 'A patient appears after requesting a review for this role.');
      const patientSelect = byId('linked-patient-select');
      if (patientSelect) {
        patientSelect.innerHTML = `<option value="">Choose a linked patient</option>${patients.map(patient => `<option value="${patient.id}">${escHtml(patient.name)}</option>`).join('')}`;
        byId('provider-medication-form').addEventListener('submit', async event => {
          event.preventDefault();
          const values = formData(event.currentTarget);
          const patientId = values.patient_id;
          delete values.patient_id;
          try {
            await api(`/api/patients/${encodeURIComponent(patientId)}/medications`, { method: 'POST', body: JSON.stringify(values) });
            byId('provider-medication-status').innerHTML = '<div class="result-item">Medicine added to the patient-owned medication list.</div>';
            location.reload();
          } catch (error) { showError(byId('provider-medication-status'), error); }
        });
      }
    }

    if (view === 'profile' && role === 'patient') {
      try {
        const profile = await fetchProfile();
        byId('profile-records').innerHTML = `<div class="dashboard-grid"><div><h3>Allergies</h3>${entryList(profile.allergies)}</div><div><h3>Conditions</h3>${entryList(profile.conditions)}</div></div><p class="disclaimer-small">Medication records are listed in My medications. Source status: ${escHtml(profile.verification)}.</p>`;
      } catch (error) { showError(byId('profile-records'), error); }
      byId('allergy-form').addEventListener('submit', async event => { event.preventDefault(); try { await postForm(event.currentTarget, '/api/profile/allergies'); location.reload(); } catch (error) { alert(error.message); } });
      byId('condition-form').addEventListener('submit', async event => { event.preventDefault(); try { await postForm(event.currentTarget, '/api/profile/conditions'); location.reload(); } catch (error) { alert(error.message); } });
    }

    if (view === 'prescriptions' && role === 'patient') {
      let latestPrescription = null;
      try {
        const result = await api('/api/prescriptions');
        byId('prescription-list').innerHTML = result.prescriptions.length ? `<div style="overflow:auto"><table class="table"><thead><tr><th>File</th><th>Status</th><th>Action</th></tr></thead><tbody>${result.prescriptions.map(item => `<tr><td>${escHtml(item.filename)}</td><td>${escHtml(item.status)}</td><td><button class="btn btn-quiet btn-small" data-preview="${item.id}">Preview</button></td></tr>`).join('')}</tbody></table></div>` : empty('No documents uploaded', 'Uploaded files are private to this patient account.');
        document.querySelectorAll('[data-preview]').forEach(button => button.addEventListener('click', async () => {
          const response = await fetch(`/api/prescriptions/${button.dataset.preview}/file`);
          if (!response.ok) return alert('Preview could not be loaded.');
          const blob = await response.blob();
          const fileUrl = URL.createObjectURL(blob);
          const dialog = document.createElement('dialog');
          dialog.className = 'document-preview';
          const preview = blob.type === 'application/pdf' ? `<iframe title="Prescription document preview" src="${fileUrl}"></iframe>` : `<img alt="Uploaded prescription preview" src="${fileUrl}">`;
          dialog.innerHTML = `<div class="document-preview__close"><button class="btn btn-quiet btn-small" type="button">Close preview</button></div>${preview}`;
          dialog.querySelector('button').addEventListener('click', () => dialog.close());
          dialog.addEventListener('close', () => { URL.revokeObjectURL(fileUrl); dialog.remove(); }, { once: true });
          document.body.append(dialog);
          dialog.showModal();
        }));
      } catch (error) { showError(byId('prescription-list'), error); }
      byId('upload-form').addEventListener('submit', async event => {
        event.preventDefault();
        const file = new FormData(event.currentTarget).get('document');
        if (!file || file.size > 5_000_000) return showError(byId('upload-message'), new Error('Choose a supported file smaller than 5 MB.'));
        try {
          const result = await api('/api/prescriptions', { method: 'POST', body: JSON.stringify({ filename: file.name, content_base64: await readBase64(file) }) });
          latestPrescription = result.id;
          byId('upload-message').innerHTML = `<div class="result-item"><strong>Stored for manual review</strong>OCR/NLP is unavailable. Nothing was extracted or approved automatically. Document ID ${result.id}.</div>`;
          location.reload();
        } catch (error) { showError(byId('upload-message'), error); }
      });
      byId('manual-confirm-form').addEventListener('submit', async event => {
        event.preventDefault();
        const existing = await api('/api/prescriptions');
        const newest = existing.prescriptions[0];
        if (!newest) return alert('Upload a prescription file first.');
        try { await api(`/api/prescriptions/${newest.id}/confirm`, { method: 'POST', body: JSON.stringify({ medications: [formData(event.currentTarget)] }) }); alert('Manual entry saved. Please review the medication list.'); location.reload(); }
        catch (error) { alert(error.message); }
      });
    }

    if (view === 'simulator' && role === 'patient') {
      byId('simulation-form').addEventListener('submit', async event => {
        event.preventDefault();
        const proposed = formData(event.currentTarget);
        try {
          const result = await api('/api/safety/simulate', { method: 'POST', body: JSON.stringify({ proposed_medicine: proposed }) });
          byId('simulation-results').innerHTML = `${panel('Before proposed medicine', resultMarkup(result.baseline || { alerts: [] }))}${panel('Preliminary simulated list', resultMarkup(result))}<p class="disclaimer-small">${escHtml(result.simulation_notice)}</p>`;
        }
        catch (error) { showError(byId('simulation-results'), error); }
      });
    }

    if (view === 'checker' && ['doctor','pharmacist'].includes(role)) {
      byId('add-professional-medication').addEventListener('click', () => {
        const row = document.createElement('div');
        row.className = 'feature-form professional-medication';
        row.innerHTML = '<input name="name" placeholder="Medicine name" required><input name="ingredient" placeholder="Active ingredient (if known)">';
        byId('professional-medications').append(row);
      });
      byId('run-professional-check').addEventListener('click', async () => {
        const medications = [...document.querySelectorAll('.professional-medication')].map(row => ({ name: row.querySelector('[name=name]').value.trim(), ingredient: row.querySelector('[name=ingredient]').value.trim() })).filter(item => item.name);
        if (!medications.length) return alert('Enter at least one medicine name.');
        try { const result = await api('/api/safety/check', { method: 'POST', body: JSON.stringify({ medications }) }); byId('professional-results').innerHTML = resultMarkup(result); }
        catch (error) { showError(byId('professional-results'), error); }
      });
    }

    if (view === 'network' || view === 'timeline' || (view === 'reports' && role === 'patient')) {
      try {
        const response = await api('/api/reports');
        if (view === 'network') {
          const latest = response.checks[0]?.results;
          const network = latest?.network;
          byId('network-view').innerHTML = !network ? empty('No saved analysis', 'Run a safety check to build a graph from its actual result.') : `<div class="network-list">${network.nodes.map(node => `<div class="network-node">${escHtml(node.label)}<br><span class="disclaimer-small">${escHtml(node.ingredient || 'Ingredient not recorded')}</span></div>`).join('') || '<span>No medication nodes</span>'}${network.edges.map(edge => `<div class="network-edge">${escHtml(network.nodes[edge.source]?.label)} ↔ ${escHtml(network.nodes[edge.target]?.label)} · ${escHtml(edge.category)}</div>`).join('') || '<div class="disclaimer-small">No duplicate-text edges in this saved check. Drug interactions were not assessed.</div>'}</div>`;
        }
        if (view === 'timeline') {
          byId('history-view').innerHTML = response.checks.length ? response.checks.slice(0, 2).map((item, index) => `<article class="action-row"><span><b>${index ? 'Previous screening' : 'Latest screening'} · #${item.id}</b><small>${new Date(item.created_at * 1000).toLocaleString()} · ${(item.results.alerts || []).length} findings</small></span><span class="badge">Snapshot</span></article>`).join('') : empty('No saved comparisons', 'Run at least one screening. Two snapshots are needed for a comparison.');
          if (response.checks.length > 1) byId('history-view').innerHTML += `<div class="result-item">Difference in finding count: ${(response.checks[0].results.alerts || []).length - (response.checks[1].results.alerts || []).length}. This compares screening summaries, not medication changes.</div>`;
        }
        if (view === 'reports' && role === 'patient') {
          byId('report-list').innerHTML = response.checks.length ? response.checks.map(item => `<article class="action-row"><span><b>Safety summary #${item.id}</b><small>${new Date(item.created_at * 1000).toLocaleString()} · ${(item.results.alerts || []).length} findings · ${escHtml(item.results.reference_status)}</small></span><button class="btn btn-quiet btn-small" data-report="${item.id}">Export JSON</button></article>`).join('') : empty('No reports saved', 'Run a check to create an exportable screening summary.');
          document.querySelectorAll('[data-report]').forEach(button => button.addEventListener('click', async () => { const report = await api(`/api/reports/${button.dataset.report}`); download(`medguard-summary-${report.id}.json`, JSON.stringify(report, null, 2), 'application/json'); }));
          byId('export-medications-json').addEventListener('click', async () => { const profile = await fetchProfile(); download('medguard-medications.json', JSON.stringify(profile.medications, null, 2), 'application/json'); });
          byId('export-medications-csv').addEventListener('click', async () => { const profile = await fetchProfile(); const rows = [['name','ingredient','strength','dose','frequency','route','duration','source','prescriber_name'], ...profile.medications.map(item => [item.name,item.ingredient,item.strength,item.dose,item.frequency,item.route,item.duration,item.source,item.prescriber_name])]; const csv = rows.map(row => row.map(value => `"${String(value || '').replaceAll('"','""')}"`).join(',')).join('\r\n'); download('medguard-medications.csv', csv, 'text/csv'); });
          byId('print-reports').addEventListener('click', () => window.print());
          document.querySelectorAll('[data-report]').forEach(button => button.addEventListener('contextmenu', event => event.preventDefault()));
        }
      } catch (error) { showError(byId(view === 'network' ? 'network-view' : view === 'timeline' ? 'history-view' : 'report-list'), error); }
    }

    if (view === 'evidence') {
      try { const result = await api('/api/evidence'); byId('evidence-view').innerHTML = `<div class="callout">${escHtml(result.message)}</div><p class="disclaimer-small">Evidence quality and medication risk severity are separate. This demo cannot classify clinical severity or provide a reference citation.</p>`; }
      catch (error) { showError(byId('evidence-view'), error); }
    }

    if (view === 'assistant') {
      const form = byId('assistant-form');
      form.addEventListener('submit', async event => { event.preventDefault(); try { const result = await postForm(form, '/api/chat'); byId('assistant-response').innerHTML = `<div class="result-item"><strong>MedGuard Assistant · fixed FAQ</strong>${escHtml(result.response)}<p class="disclaimer-small">${escHtml(result.assistant_mode)}</p></div>`; } catch (error) { showError(byId('assistant-response'), error); } });
      document.querySelectorAll('[data-chat-prompt]').forEach(button => button.addEventListener('click', async () => { form.elements.question.value = button.dataset.chatPrompt; form.requestSubmit(); }));
    }

    if (view === 'appointments') {
      try {
        const result = await api('/api/appointments');
        byId('appointment-list').innerHTML = result.appointments.length ? result.appointments.map(item => `<article class="action-row"><span><b>${escHtml(item.professional_role)} · ${escHtml(item.status)}</b><small>${escHtml(item.requested_for || 'Time not specified')} · ${new Date(item.created_at * 1000).toLocaleString()}</small></span>${role === 'patient' && item.status === 'Requested' ? `<button class="btn btn-quiet btn-small" data-cancel-appointment="${item.id}">Cancel request</button>` : ''}${['doctor','pharmacist'].includes(role) && item.professional_role === role && item.status === 'Requested' ? `<button class="btn btn-quiet btn-small" data-confirm-appointment="${item.id}">Confirm (simulated)</button>` : ''}</article>`).join('') : empty('No appointment requests', 'Requests use synthetic availability only.');
        document.querySelectorAll('[data-cancel-appointment]').forEach(button => button.addEventListener('click', async () => { await api(`/api/appointments/${button.dataset.cancelAppointment}/cancel`, { method: 'POST', body: '{}' }); location.reload(); }));
        document.querySelectorAll('[data-confirm-appointment]').forEach(button => button.addEventListener('click', async () => { await api(`/api/appointments/${button.dataset.confirmAppointment}/status`, { method: 'POST', body: JSON.stringify({ status: 'Confirmed' }) }); location.reload(); }));
      } catch (error) { showError(byId('appointment-list'), error); }
      const form = byId('appointment-form');
      if (form && role === 'patient') form.addEventListener('submit', async event => { event.preventDefault(); try { await postForm(form, '/api/appointments'); location.reload(); } catch (error) { alert(error.message); } });
      if (form && role !== 'patient') form.remove();
    }

    if (view === 'schedule' && role === 'patient') {
      try {
        const [schedules, profile] = await Promise.all([api('/api/schedules'), fetchProfile()]);
        byId('schedule-list').innerHTML = schedules.schedules.length ? schedules.schedules.map(item => `<article class="action-row"><span><b>${escHtml(item.name)} · ${escHtml(item.time_label)}</b><small>${escHtml(item.dose || 'Dose not recorded')} · ${escHtml(item.frequency || 'Frequency not recorded')}</small></span><button class="btn btn-quiet btn-small" data-adherence="${item.id}" data-status="taken">Record taken</button><button class="btn btn-quiet btn-small" data-adherence="${item.id}" data-status="missed">Record missed</button></article>`).join('') : empty('No schedule labels', 'Add a label based on the confirmed prescription; timing is not changed by this app.');
        byId('schedule-medication').innerHTML = `<option value="">Choose a medication</option>${profile.medications.map(item => `<option value="${item.id}">${escHtml(item.name)}</option>`).join('')}`;
        document.querySelectorAll('[data-adherence]').forEach(button => button.addEventListener('click', async () => { await api('/api/adherence', { method: 'POST', body: JSON.stringify({ schedule_id: Number(button.dataset.adherence), status: button.dataset.status }) }); location.reload(); }));
      } catch (error) { showError(byId('schedule-list'), error); }
      byId('schedule-form').addEventListener('submit', async event => { event.preventDefault(); const values = formData(event.currentTarget); values.reminder_enabled = event.currentTarget.elements.reminder_enabled.checked; try { await api('/api/schedules', { method: 'POST', body: JSON.stringify(values) }); location.reload(); } catch (error) { alert(error.message); } });
    }

    if (view === 'caregiver' && role === 'patient') {
      byId('caregiver-grant-form').addEventListener('submit', async event => { event.preventDefault(); try { await postForm(event.currentTarget, '/api/caregiver-consents'); byId('caregiver-status').innerHTML = '<div class="result-item">Permission saved. The caregiver must use the matching demo account.</div>'; } catch (error) { showError(byId('caregiver-status'), error); } });
      try {
        const result = await api('/api/caregiver-consents');
        byId('patient-consents').innerHTML = result.consents.length ? result.consents.map(item => `<article class="action-row"><span><b>${escHtml(item.caregiver_name)} · ${escHtml(item.permission)}</b><small>${escHtml(item.email)} · ${item.active ? 'Access active' : 'Revoked'}</small></span>${item.active ? `<button class="btn btn-quiet btn-small" data-revoke-consent="${item.id}">Revoke</button>` : ''}</article>`).join('') : empty('No permissions granted', 'A caregiver account receives no data until you grant a specific scope.');
        document.querySelectorAll('[data-revoke-consent]').forEach(button => button.addEventListener('click', async () => { await api(`/api/caregiver-consents/${button.dataset.revokeConsent}/revoke`, { method: 'POST', body: '{}' }); location.reload(); }));
      } catch (error) { showError(byId('patient-consents'), error); }
    }
    if (view === 'dependents' && role === 'caregiver') {
      try { const result = await api('/api/caregiver/dependents'); byId('dependent-list').innerHTML = result.dependents.length ? result.dependents.map(item => `<article class="feature-item"><strong>${escHtml(item.name)} · ${escHtml(item.permission)} permission</strong>${item.medications ? item.medications.map(med => `<p>${escHtml(med.name)} · ${escHtml(med.strength)} · ${escHtml(med.schedule)}<br><span class="disclaimer-small">${escHtml(med.source || 'Patient-entered')}${med.prescriber_name ? ` · ${escHtml(med.prescriber_name)}` : ''}</span></p>`).join('') : ''}${item.reports ? `<p>${item.reports.length} authorized safety summaries available. Each may be incomplete.</p>` : ''}${!item.medications && !item.reports ? '<p>No details are included for this scope.</p>' : ''}</article>`).join('') : empty('No authorized dependents', 'A patient must explicitly grant a scope first.'); }
      catch (error) { showError(byId('dependent-list'), error); }
    }

    if (view === 'schedule' && role === 'caregiver') {
      try {
        const result = await api('/api/caregiver/dependents');
        const schedules = result.dependents.flatMap(dependent => (dependent.schedules || []).map(schedule => ({ ...schedule, dependent: dependent.name })));
        byId('caregiver-schedules').innerHTML = schedules.length ? schedules.map(schedule => `<article class="action-row"><span><b>${escHtml(schedule.dependent)} · ${escHtml(schedule.name)} · ${escHtml(schedule.time_label)}</b><small>${escHtml(schedule.dose || 'Dose not recorded')} · ${escHtml(schedule.frequency || 'Frequency not recorded')}</small></span><button class="btn btn-quiet btn-small" data-caregiver-adherence="${schedule.id}" data-status="taken">Record taken</button><button class="btn btn-quiet btn-small" data-caregiver-adherence="${schedule.id}" data-status="missed">Record missed</button></article>`).join('') : empty('No shared schedules', 'A patient must grant schedule scope before schedules are visible.');
        document.querySelectorAll('[data-caregiver-adherence]').forEach(button => button.addEventListener('click', async () => { await api('/api/caregiver/adherence', { method: 'POST', body: JSON.stringify({ schedule_id: Number(button.dataset.caregiverAdherence), status: button.dataset.status }) }); alert('Adherence record saved.'); }));
      } catch (error) { showError(byId('caregiver-schedules'), error); }
    }

    if (view === 'notifications') {
      try {
        const result = await api('/api/notifications');
        byId('notification-list').innerHTML = result.notifications.length ? result.notifications.map(item => `<article class="action-row"><span><b>${escHtml(item.category)}${item.is_read ? ' · Read' : ' · New'}</b><small>${escHtml(item.message)} · ${new Date(item.created_at * 1000).toLocaleString()}</small></span>${item.is_read ? '' : `<button class="btn btn-quiet btn-small" data-read-notification="${item.id}">Mark read</button>`}</article>`).join('') : empty('No notifications', 'In-app safety and review events appear here.');
        document.querySelectorAll('[data-read-notification]').forEach(button => button.addEventListener('click', async () => { await api(`/api/notifications/${button.dataset.readNotification}/read`, { method: 'POST', body: '{}' }); location.reload(); }));
      } catch (error) { showError(byId('notification-list'), error); }
    }

    if (view === 'analytics' && role === 'admin') {
      try { const result = await api('/api/admin/analytics'); byId('analytics-view').innerHTML = `<div class="metric-grid">${Object.entries(result.aggregate_metrics).map(([key,value]) => `<article class="metric glass"><div class="metric-head">${escHtml(key.replaceAll('_',' '))}</div><strong>${value}</strong></article>`).join('')}</div><p class="disclaimer-small">Patient-level records are not included: ${!result.patient_details_included ? 'confirmed' : 'not confirmed'}.</p>`; }
      catch (error) { showError(byId('analytics-view'), error); }
    }
    if (view === 'audit' && role === 'admin') {
      try { const result = await api('/api/admin/audit-logs'); byId('audit-view').innerHTML = result.audit_logs.length ? `<div style="overflow:auto"><table class="table"><thead><tr><th>Actor role</th><th>Action</th><th>Resource</th><th>Time</th></tr></thead><tbody>${result.audit_logs.map(item => `<tr><td>${escHtml(item.actor_role || 'Deleted user')}</td><td>${escHtml(item.action)}</td><td>${escHtml(item.resource_type)}</td><td>${new Date(item.created_at * 1000).toLocaleString()}</td></tr>`).join('')}</tbody></table></div>` : empty('No audit events', 'Sensitive demo workflows create metadata-only events.'); }
      catch (error) { showError(byId('audit-view'), error); }
    }

    if (view === 'capabilities') {
      const selector = byId('glossary-language');
      selector.addEventListener('change', () => {
        byId('glossary-note').textContent = selector.value === 'te' ? 'இது ஒரு கல்வி நோக்கத்திற்கான முன்மாதிரி. மருத்துவ ஆதாரத் தரவு இணைக்கப்படவில்லை.' : 'Prototype coverage is explicit; clinical source integrations are not bundled.';
      });
    }
  }
})();
