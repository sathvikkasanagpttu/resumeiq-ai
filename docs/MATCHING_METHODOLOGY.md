# RESUMEIQ — Matching Methodology

## 1. Candidate–Job Compatibility Score Formulation

Never presented as a generic or black-box "ATS Score", the **Candidate–Job Compatibility Score** is calculated through a transparent, multi-signal weighted combination:

$$\text{CompatibilityScore} = \frac{\sum_{i=1}^{N} w_i \cdot S_i}{\sum_{i=1}^{N} w_i}$$

Where $S_i \in [0, 100]$ represents the component score for signal $i$, and $w_i$ represents the configurable weight for that signal.

---

## 2. The 8 Core Component Signals

### 1. Required Skill Coverage ($S_{\text{req}}$) — Default Weight: 0.25
Evaluates coverage across all mandatory qualifications:
$$S_{\text{req}} = \frac{1}{|K_{\text{req}}|} \sum_{k \in K_{\text{req}}} \text{MatchScore}(k, \text{CandidateSkills})$$
Where `MatchScore` evaluates:
- **Exact Match:** $1.0$ (Canonical skill identity)
- **Child Skill:** $0.90$ (e.g., job asks for Python, candidate has FastAPI)
- **Parent Skill:** $0.75$ (e.g., job asks for FastAPI, candidate has Python)
- **Transferable Affinity:** $0.50 - 0.85$ (e.g., AWS to GCP = $0.85$)
- **Missing:** $0.00$

### 2. Semantic Fit ($S_{\text{sem}}$) — Default Weight: 0.20
Calculates dense vector embedding cosine similarity between the job description corpus and the candidate resume corpus:
$$\text{Sim}_{\text{dense}}(\mathbf{u}, \mathbf{v}) = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\| \|\mathbf{v}\|} \times 100$$

### 3. Evidence Strength ($S_{\text{ev}}$) — Default Weight: 0.15
Proportion of candidate skills that are demonstrated with active verbs and quantifiable metrics rather than listed passively.
$$S_{\text{ev}} = \min\left(100, \frac{\text{VerifiedSkillsCount}}{\text{TotalSkillsCount}} \times 120\right)$$

### 4. Experience Alignment ($S_{\text{exp}}$) — Default Weight: 0.15
Measures candidate verified tenure against minimum listed years of experience. If candidate meets or exceeds the required threshold, $S_{\text{exp}} = 100$.

### 5. Preferred Skill Coverage ($S_{\text{pref}}$) — Default Weight: 0.08
Proportion of nice-to-have or bonus domain capabilities present in the candidate profile.

### 6. Seniority Alignment ($S_{\text{sen}}$) — Default Weight: 0.07
Evaluates structural career tier congruence (Entry, Mid, Senior, Lead, Staff, Principal).

### 7. Domain Alignment ($S_{\text{dom}}$) — Default Weight: 0.05
Cross-functional technological breadth (Backend, Frontend, Cloud/DevOps, AI/Data, Distributed Systems).

### 8. Education & Credentials ($S_{\text{edu}}$) — Default Weight: 0.05
Academic background and certified industry credentials matching stated job qualifications.

---

## 3. Configurable Weights

The weighting model is completely customizable through the UI or API request (`/api/v1/matching`), allowing recruiters and candidates to recalibrate based on specific hiring criteria (e.g. prioritizing evidence depth over pure keyword coverage).
