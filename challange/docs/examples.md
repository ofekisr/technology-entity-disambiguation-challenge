# Resolve examples

Every case below ran through the real resolver on index `9d402f5cc5a9ad38` (178 entities, 802 aliases).
Each row shows where the match happened and the numbers behind the answer.
Rule (D-22, D-48): `resolved` iff raw score ≥ 0.75 and margin ≥ 0.15; `ambiguous` iff score ≥ 0.5; else `no_match`.
Hints and the vendor found in the input add a bonus of 0.15 that ranks and widens the margin, never the raw score.

Steps: **A** = exact on the input as typed (ExactAlias, JoinedWords, WithoutNumbers); **B** = SynonymRewrite, then the exact steps again and FuzzyAlias.

Regenerate with `make examples`. Interactive version with full traces: guide › Examples tab.

## Exact names

| Input | Matched at | Final answer | Why | Expected |
|---|---|---|---|---|
| `Amazon EKS` | A · ExactAlias | resolved `aws/eks` · 0.9 | raw 0.9 · margin 0.9 | ✅ |
| `Amazon Elastic Kubernetes Service` | A · ExactAlias | resolved `aws/eks` · 0.97 | raw 0.97 · margin 0.97 | ✅ |
| `Amazon Web Services` | A · ExactAlias | resolved `aws/aws` · 0.97 | raw 0.97 · margin 0.97 | ✅ |
| `Apache Log4j 2.14` | A · ExactAlias | resolved `apache/log4j` · 1.0 | raw 1.0 · margin 1.0 | ✅ |
| `Atlassian SourceTree` | A · ExactAlias | resolved `atlassian/sourcetree` · 1.0 | raw 1.0 · margin 1.0 | ✅ |
| `AWS` | A · ExactAlias | resolved `aws/aws` · 0.8 | raw 0.8 · margin 0.8 | ✅ |
| `AWS Cloud` | A · ExactAlias | resolved `aws/aws` · 0.97 | raw 0.97 · margin 0.97 | ✅ |
| `AWS EKS` | A · ExactAlias | resolved `aws/eks` · 1.0 | raw 1.0 · margin 1.0 | ✅ |
| `CrowdStrike Falcon` | A · ExactAlias | resolved `crowdstrike/falcon` · 1.0 | raw 1.0 · margin 1.0 | ✅ |
| `EKS` | A · ExactAlias | resolved `aws/eks` · 0.8 | raw 0.8 · margin 0.8 | ✅ |
| `Experience Manager (AEM) Forms` | A · ExactAlias | resolved `adobe/experience_manager_forms` · 0.97 | raw 0.97 · margin 0.97 | ✅ |
| `F5 NGINX` | A · ExactAlias | resolved `nginx/nginx` · 0.9 | raw 0.9 · margin 0.9 | ✅ |
| `k8s` | A · ExactAlias | resolved `kubernetes/kubernetes` · 0.8 | raw 0.8 · margin 0.8 | ✅ |
| `log4j` | A · ExactAlias | resolved `apache/log4j` · 0.8 | raw 0.8 · margin 0.8 | ✅ |
| `Log4j2` | A · ExactAlias | resolved `apache/log4j` · 0.97 | raw 0.97 · margin 0.97 | ✅ |
| `Microsoft` | A · ExactAlias | resolved `microsoft/*` · 1.0 | raw 1.0 · margin 1.0 | ✅ |
| `Nginx` | A · ExactAlias | resolved `nginx/nginx` · 1.0 | raw 1.0 · margin 1.0 | ✅ |
| `VS Code` | A · ExactAlias | resolved `microsoft/visual_studio_code` · 0.97 | raw 0.97 · margin 0.97 | ✅ |

## Near-collisions

| Input | Matched at | Final answer | Why | Expected |
|---|---|---|---|---|
| `Azure Sentinel` | A · ExactAlias | resolved `microsoft/sentinel` · 0.97 | raw 0.97 · margin 0.97 | ✅ |
| `Falcon` | A · ExactAlias | ambiguous · `crowdstrike/falcon` 0.5, `falconry/falcon` 0.5 | raw 0.8 · margin 0.0 | ✅ |
| `Falcon EDR` | A · ExactAlias | resolved `crowdstrike/falcon` · 0.9 | raw 0.9 · margin 0.9 | ✅ |
| `Microsoft Sentinel` | A · ExactAlias | resolved `microsoft/sentinel` · 1.0 | raw 1.0 · margin 1.0 | ✅ |
| `Sentinel` | A · ExactAlias | ambiguous · `hashicorp/sentinel` 0.3333, `microsoft/sentinel` 0.3333, `thales/sentinel` 0.3333 | raw 0.8 · margin 0.0 | ✅ |
| `Sentinel SIEM` | A · ExactAlias | resolved `microsoft/sentinel` · 0.9 | raw 0.9 · margin 0.9 | ✅ |
| `SentinelOne` | A · ExactAlias | resolved `sentinelone/sentinelone` · 1.0 | raw 1.0 · margin 1.0 | ✅ |

## Hard negatives

| Input | Matched at | Final answer | Why | Expected |
|---|---|---|---|---|
| `Amazon` | A · ExactAlias | resolved `amazon/*` · 1.0 | raw 1.0 · margin 1.0 | ✅ |
| `Amazon Prime` | B · FuzzyAlias | no_match | raw 0.2835 · margin 0.2835 | ✅ |
| `C` | A · ExactAlias | resolved `c/c` · 0.8 | raw 0.8 · margin 0.8 | ✅ |
| `C#` | A · ExactAlias | resolved `csharp/csharp` · 0.8 | raw 0.8 · margin 0.8 | ✅ |
| `C++` | A · ExactAlias | resolved `cpp/cpp` · 0.8 | raw 0.8 · margin 0.8 | ✅ |
| `Dynamics 365` | — | no_match | nothing matched | ✅ |
| `GitHub Copilot` | A · ExactAlias | resolved `github/copilot` · 1.0 | raw 1.0 · margin 1.0 | ✅ |
| `Google` | A · ExactAlias | resolved `google/*` · 1.0 | raw 1.0 · margin 1.0 | ✅ |
| `Google Cloud` | A · ExactAlias | resolved `google/cloud` · 1.0 | raw 1.0 · margin 1.0 | ✅ |
| `Microsoft 365` | — | no_match | nothing matched | ✅ |
| `Microsoft Copilot` | A · ExactAlias | resolved `microsoft/copilot` · 1.0 | raw 1.0 · margin 1.0 | ✅ |
| `Microsoft Defender for Cloud` | B · FuzzyAlias | ambiguous · `microsoft/defender_for_endpoint` 0.5941, `microsoft/azure` 0.4059 | raw 0.6087 · +bonus → rank 0.7587 · margin 0.2403 | ✅ not resolved (gold: no_match) |
| `Office 365` | B · FuzzyAlias | no_match | raw 0.3658 · margin 0.3658 | ✅ |
| `Splunk Enterprise Security` | B · FuzzyAlias | ambiguous · `splunk/enterprise` 1.0 | raw 0.6871 · +bonus → rank 0.8371 · margin 0.5783 | ✅ not resolved (gold: no_match) |

## Typos

| Input | Matched at | Final answer | Why | Expected |
|---|---|---|---|---|
| `Crowdstrik Falcon` | B · FuzzyAlias | resolved `crowdstrike/falcon` · 0.948 | raw 0.948 · margin 0.4678 | ✅ |
| `Crowdstrike Falcn` (rank above 1, confidence stays raw) | B · FuzzyAlias | resolved `crowdstrike/falcon` · 0.904 | raw 0.904 · +bonus → rank 1.054 · margin 0.6698 | ✅ |

## Paraphrases (semantic layer)

| Input | Matched at | Final answer | Why | Expected |
|---|---|---|---|---|
| `Amazon Kubernetes` | A · ExactAlias | resolved `aws/eks` · 0.8 | raw 0.8 · margin 0.8 | ✅ |
| `Amazon managed k8` | B · ExactAlias | resolved `aws/eks` · 0.8 | raw 0.8 · margin 0.8 | ✅ |
| `AWS managed Kubernetes` | A · ExactAlias | resolved `aws/eks` · 0.8 | raw 0.8 · margin 0.8 | ✅ |
| `Fortinet firewall` | A · ExactAlias | resolved `fortinet/fortigate` · 0.8 | raw 0.8 · margin 0.8 | ✅ |
| `Google managed Kubernetes` | A · ExactAlias | resolved `google/kubernetes_engine` · 0.8 | raw 0.8 · margin 0.8 | ✅ |
| `managed kubernetes` | B · FuzzyAlias | ambiguous · `aws/eks` 0.5275, `google/kubernetes_engine` 0.4725 | raw 0.7673 · margin 0.08 | ✅ |
| `MS Teams` | A · ExactAlias | resolved `microsoft/teams` · 0.9 | raw 0.9 · margin 0.9 | ✅ |
| `Sentinel One` | A · JoinedWords | resolved `sentinelone/sentinelone` · 1.0 | raw 1.0 · margin 1.0 | ✅ |

## Normalization retries

| Input | Matched at | Final answer | Why | Expected |
|---|---|---|---|---|
| `Log4j 2` | A · ExactAlias | resolved `apache/log4j` · 0.97 | raw 0.97 · margin 0.97 | ✅ |
| `MS` | B · FuzzyAlias | ambiguous · `microsoft/windows` 0.2035, `microsoft/windows_server` 0.2035, `microsoft/azure` 0.2017 | raw 0.4442 · +bonus → rank 0.5942 · margin 0.0 | ✅ |
| `Share Point` | A · JoinedWords | resolved `microsoft/sharepoint` · 0.8 | raw 0.8 · margin 0.8 | ✅ |
| `Windows 10` | A · WithoutNumbers | resolved `microsoft/windows` · 0.8 | raw 0.8 · margin 0.8 | ✅ |

## Hints and filters

| Input | Matched at | Final answer | Why | Expected |
|---|---|---|---|---|
| `Falcon` (category=edr) | A · ExactAlias | resolved `crowdstrike/falcon` · 0.8 | raw 0.8 · +bonus → rank 0.95 · margin 0.15 | ✅ |
| `Sentinel` (vendor=microsoft) | A · ExactAlias | resolved `microsoft/sentinel` · 0.8 | raw 0.8 · +bonus → rank 0.95 · margin 0.15 | ✅ |
| `Sentinel` (filter vendors=hashicorp) | A · ExactAlias | resolved `hashicorp/sentinel` · 0.8 | raw 0.8 · margin 0.8 | ✅ |

## Unknown names

| Input | Matched at | Final answer | Why | Expected |
|---|---|---|---|---|
| `Acme Widget Pro` | — | no_match | nothing matched | ✅ |
| `AWS Foo` | — | no_match | nothing matched | ✅ |
| `Totally Unknown Thing` | — | no_match | nothing matched | ✅ |

## Known limits

| Input | Matched at | Final answer | Why | Expected |
|---|---|---|---|---|
| `AWS EKS cluster` (G-05: an extra generic word) | B · FuzzyAlias | ambiguous · `aws/eks` 1.0 | raw 0.5578 · +bonus → rank 0.7078 · margin 0.7078 | gap · want resolved `aws/eks` |
| `Crwdstrk Falcon` (more than 2 letters wrong) | B · FuzzyAlias | no_match | raw 0.4226 · margin 0.0 | gap · want resolved `crowdstrike/falcon` |
| `RedHat` (joined word, split not handled) | — | no_match | nothing matched | gap · want resolved `redhat/enterprise_linux` |

## Appendix — optional (+5 minutes)

One full trace per kind: the data each step read.

### Exact names: `Amazon EKS`

Normalized: `amazon eks`

- **A · ExactAlias** on `amazon eks` → hit
  - alias `amazon eks` → `aws/eks` (generated, base 0.9)
- **Decide:** top `aws/eks` raw 0.9 (≥ 0.75: yes), margin 0.9 (≥ 0.15: yes) → resolved `aws/eks` · 0.9
- **Final answer:** resolved → aws/eks (AWS EKS), confidence 0.9. Confidence = raw 0.9 after calibration, capped at 1.0.

### Near-collisions: `Azure Sentinel`

Normalized: `azure sentinel`

- **A · ExactAlias** on `azure sentinel` → hit
  - alias `azure sentinel` → `microsoft/sentinel` (strong, base 0.97)
- **Decide:** top `microsoft/sentinel` raw 0.97 (≥ 0.75: yes), margin 0.97 (≥ 0.15: yes) → resolved `microsoft/sentinel` · 0.97
- **Final answer:** resolved → microsoft/sentinel (Microsoft Sentinel), confidence 0.97. Confidence = raw 0.97 after calibration, capped at 1.0.

### Hard negatives: `Amazon Prime`

Normalized: `amazon prime`

- **A · ExactAlias** on `amazon prime` → miss
- **A · JoinedWords** on `amazon prime` → miss
- **A · WithoutNumbers** on `amazon prime` → miss
- **B · SynonymRewrite** on `amazon prime` → no change
- **B · ExactAlias** on `amazon prime` → miss
- **B · JoinedWords** on `amazon prime` → miss
- **B · WithoutNumbers** on `amazon prime` → miss
- **B · FuzzyAlias** on `amazon prime` → hit
  - `paloaltonetworks/prisma_cloud` via `prisma cloud`: common prisma 5.2807 = 3.1684 / union 11.1778 = raw 0.2835
- **Decide:** top `paloaltonetworks/prisma_cloud` raw 0.2835 (≥ 0.75: no), margin 0.2835 (≥ 0.15: yes) → no_match
- **Final answer:** no_match → confidence 0.0; the input goes to the review queue. Top rank 0.2835 is below t_low.

### Typos: `Crowdstrik Falcon`

Normalized: `crowdstrik falcon`

- **A · ExactAlias** on `crowdstrik falcon` → miss
- **A · JoinedWords** on `crowdstrik falcon` → miss
- **A · WithoutNumbers** on `crowdstrik falcon` → miss
- **B · SynonymRewrite** on `crowdstrik falcon` → no change
- **B · ExactAlias** on `crowdstrik falcon` → miss
- **B · JoinedWords** on `crowdstrik falcon` → miss
- **B · WithoutNumbers** on `crowdstrik falcon` → miss
- **B · FuzzyAlias** on `crowdstrik falcon` → hit
  - `crowdstrike/falcon` via `crowdstrike falcon`: common crowdstrike 5.2807 + falcon 4.8777 = 9.6303 / union 10.1584 = raw 0.948
  - `falconry/falcon` via `falcon`: common falcon 4.8777 = 4.8777 / union 10.1584 = raw 0.4802
  - `crowdstrike/*` via `crowdstrike`: common crowdstrike 5.2807 = 4.7526 / union 10.1584 = raw 0.4678
- **Decide:** top `crowdstrike/falcon` raw 0.948 (≥ 0.75: yes), margin 0.4678 (≥ 0.15: yes) → resolved `crowdstrike/falcon` · 0.948
- **Final answer:** resolved → crowdstrike/falcon (CrowdStrike Falcon), confidence 0.948. Confidence = raw 0.948 after calibration, capped at 1.0.

### Paraphrases (semantic layer): `managed kubernetes`

Normalized: `managed kubernetes`

- **A · ExactAlias** on `managed kubernetes` → miss
- **A · JoinedWords** on `managed kubernetes` → miss
- **A · WithoutNumbers** on `managed kubernetes` → miss
- **B · SynonymRewrite** on `managed kubernetes` → no change
- **B · ExactAlias** on `managed kubernetes` → miss
- **B · JoinedWords** on `managed kubernetes` → miss
- **B · WithoutNumbers** on `managed kubernetes` → miss
- **B · FuzzyAlias** on `managed kubernetes` → hit
  - `aws/eks` via `amazon managed kubernetes`: common kubernetes 3.7414 + managed 4.372 = 8.1134 / union 10.574 = raw 0.7673
  - `google/kubernetes_engine` via `google managed kubernetes`: common kubernetes 3.7414 + managed 4.372 = 8.1134 / union 11.8048 = raw 0.6873
  - `kubernetes/kubernetes` via `kubernetes`: common kubernetes 3.7414 = 3.7414 / union 8.1134 = raw 0.4611
- **Decide:** top `aws/eks` raw 0.7673 (≥ 0.75: yes), margin 0.08 (≥ 0.15: no) → ambiguous · `aws/eks` 0.5275, `google/kubernetes_engine` 0.4725
- **Final answer:** ambiguous → the caller picks one of: aws/eks 0.5275, google/kubernetes_engine 0.4725; confidence 0.7673. Confidence = top rank 0.7673 after calibration, capped at 1.0; shares = each rank ÷ sum of shown ranks.

### Normalization retries: `MS`

Normalized: `ms`

- **A · ExactAlias** on `ms` → miss
- **A · JoinedWords** on `ms` → miss
- **A · WithoutNumbers** on `ms` → miss
- **B · SynonymRewrite** on `ms` → no change
- **B · ExactAlias** on `ms` → miss
- **B · JoinedWords** on `ms` → miss
- **B · WithoutNumbers** on `ms` → miss
- **B · FuzzyAlias** on `ms` → hit
  - `microsoft/windows` via `ms os`: common ms 2.6892 = 2.6892 / union 6.054 = raw 0.4442
  - `microsoft/windows_server` via `ms os`: common ms 2.6892 = 2.6892 / union 6.054 = raw 0.4442
  - `microsoft/azure` via `ms cloud`: common ms 2.6892 = 2.6892 / union 6.1256 = raw 0.439
- **Decide:** top `microsoft/windows` raw 0.4442 (≥ 0.75: no), margin 0.0 (≥ 0.15: no) → ambiguous · `microsoft/windows` 0.2035, `microsoft/windows_server` 0.2035, `microsoft/azure` 0.2017
- **Final answer:** ambiguous → the caller picks one of: microsoft/windows 0.2035, microsoft/windows_server 0.2035, microsoft/azure 0.2017, microsoft/sql_server 0.2017, microsoft/exchange_server 0.1896; confidence 0.5942. Confidence = top rank 0.5942 (raw 0.4442 + bonus) after calibration, capped at 1.0; shares = each rank ÷ sum of shown ranks.

### Hints and filters: `Falcon` (category=edr)

Normalized: `falcon`

- **A · ExactAlias** on `falcon` → hit
  - alias `falcon` → `crowdstrike/falcon` (weak, base 0.8)
  - alias `falcon` → `falconry/falcon` (weak, base 0.8)
- **Decide:** top `crowdstrike/falcon` raw 0.8 (≥ 0.75: yes), margin 0.15 (≥ 0.15: yes) → resolved `crowdstrike/falcon` · 0.8
- **Final answer:** resolved → crowdstrike/falcon (CrowdStrike Falcon), confidence 0.8. Confidence = raw 0.8 after calibration, capped at 1.0; rank 0.95 = raw 0.8 + bonus only ordered the candidates.

### Unknown names: `Acme Widget Pro`

Normalized: `acme widget pro`

- **A · ExactAlias** on `acme widget pro` → miss
- **A · JoinedWords** on `acme widget pro` → miss
- **A · WithoutNumbers** on `acme widget pro` → miss
- **B · SynonymRewrite** on `acme widget pro` → no change
- **B · ExactAlias** on `acme widget pro` → miss
- **B · JoinedWords** on `acme widget pro` → miss
- **B · WithoutNumbers** on `acme widget pro` → miss
- **B · FuzzyAlias** on `acme widget pro` → miss

### Known limits: `AWS EKS cluster`

Normalized: `aws eks cluster`

- **A · ExactAlias** on `aws eks cluster` → miss
- **A · JoinedWords** on `aws eks cluster` → miss
- **A · WithoutNumbers** on `aws eks cluster` → miss
- **B · SynonymRewrite** on `aws eks cluster` → no change
- **B · ExactAlias** on `aws eks cluster` → miss
- **B · JoinedWords** on `aws eks cluster` → miss
- **B · WithoutNumbers** on `aws eks cluster` → miss
- **B · FuzzyAlias** on `aws eks cluster` → hit
  - `aws/eks` via `aws eks`: common aws 3.1233 + eks 5.2807 = 8.404 / union 15.0671 = raw 0.5578
- **Decide:** top `aws/eks` raw 0.5578 (≥ 0.75: no), margin 0.7078 (≥ 0.15: yes) → ambiguous · `aws/eks` 1.0
- **Final answer:** ambiguous → the caller picks one of: aws/eks 1.0; confidence 0.7078. Confidence = top rank 0.7078 (raw 0.5578 + bonus) after calibration, capped at 1.0; shares = each rank ÷ sum of shown ranks.
