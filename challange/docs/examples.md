# Resolve examples

Every case below ran through the real resolver on index `9d402f5cc5a9ad38` (178 entities, 802 aliases).
Each row shows where the match happened and the numbers behind the answer.
Rule (D-22, D-48): `resolved` iff raw score ≥ 0.75 and margin ≥ 0.15; `ambiguous` iff raw score ≥ 0.5 (D-51: candidates below are dropped); else `no_match`.
Hints and the vendor found in the input add a bonus of 0.15 that ranks and widens the margin, never the raw score.

Steps: **A** = exact on the input as typed (ExactAlias, JoinedWords, CamelCaseSplit, WithoutNumbers); **B** = SynonymRewrite, then ExactAlias, JoinedWords, WithoutNumbers and FuzzyAlias.

Regenerate with `make examples`. Interactive version with full traces: guide › Examples tab.

## Exact name or alias

The input is already in the alias table; the alias strength sets the score: canonical 1.0, curated 0.97, generated 0.9, weak 0.8.

| Input | Matched at | Final answer | Why | Expected |
|---|---|---|---|---|
| `CrowdStrike Falcon` (canonical name) | A · ExactAlias | resolved `crowdstrike/falcon` · 1.0 | raw 1.0 · margin 1.0 | ✅ |
| `Amazon Elastic Kubernetes Service` (curated full name) | A · ExactAlias | resolved `aws/eks` · 0.97 | raw 0.97 · margin 0.97 | ✅ |
| `F5 NGINX` (generated vendor × product) | A · ExactAlias | resolved `nginx/nginx` · 0.9 | raw 0.9 · margin 0.9 | ✅ |
| `EKS` (weak: a bare acronym) | A · ExactAlias | resolved `aws/eks` · 0.8 | raw 0.8 · margin 0.8 | ✅ |

## Vendor names and prefixes

A bare vendor name maps to the vendor entity; a prefix such as MS only counts next to a product (D-41).

| Input | Matched at | Final answer | Why | Expected |
|---|---|---|---|---|
| `Microsoft` (vendor entity) | A · ExactAlias | resolved `microsoft/*` · 1.0 | raw 1.0 · margin 1.0 | ✅ |
| `MS Teams` (prefix next to a product (G-06)) | A · ExactAlias | resolved `microsoft/teams` · 0.9 | raw 0.9 · margin 0.9 | ✅ |
| `MS` (a prefix alone never resolves) | B · FuzzyAlias | no_match | best raw 0.4442 is below t_low 0.5 | ✅ |

## Look-alikes kept apart

Names that share letters or words but are different products each resolve to their own id.

| Input | Matched at | Final answer | Why | Expected |
|---|---|---|---|---|
| `C` | A · ExactAlias | resolved `c/c` · 0.8 | raw 0.8 · margin 0.8 | ✅ |
| `C#` (symbols are kept) | A · ExactAlias | resolved `csharp/csharp` · 0.8 | raw 0.8 · margin 0.8 | ✅ |
| `C++` (symbols are kept) | A · ExactAlias | resolved `cpp/cpp` · 0.8 | raw 0.8 · margin 0.8 | ✅ |
| `Microsoft Copilot` | A · ExactAlias | resolved `microsoft/copilot` · 1.0 | raw 1.0 · margin 1.0 | ✅ |
| `GitHub Copilot` | A · ExactAlias | resolved `github/copilot` · 1.0 | raw 1.0 · margin 1.0 | ✅ |
| `SentinelOne` (not Microsoft Sentinel) | A · ExactAlias | resolved `sentinelone/sentinelone` · 1.0 | raw 1.0 · margin 1.0 | ✅ |

## Cleaning and retries

Versions are dropped, split words are joined, CamelCase is split at inner capitals, a trailing number is retried without it.

| Input | Matched at | Final answer | Why | Expected |
|---|---|---|---|---|
| `Apache Log4j 2.14` (dotted version dropped) | A · ExactAlias | resolved `apache/log4j` · 1.0 | raw 1.0 · margin 1.0 | ✅ |
| `Log4j 2` (bare number kept) | A · ExactAlias | resolved `apache/log4j` · 0.97 | raw 0.97 · margin 0.97 | ✅ |
| `Share Point` (split words joined) | A · JoinedWords | resolved `microsoft/sharepoint` · 0.8 | raw 0.8 · margin 0.8 | ✅ |
| `Windows 10` (retried without the number) | A · WithoutNumbers | resolved `microsoft/windows` · 0.8 | raw 0.8 · margin 0.8 | ✅ |
| `RedHat` (split at inner capitals (D-50)) | A · CamelCaseSplit | resolved `redhat/*` · 1.0 | raw 1.0 · margin 1.0 | ✅ |

## Same name, different products

A bare shared name is ambiguous; a hint, a filter or a context word picks one (D-48).

| Input | Matched at | Final answer | Why | Expected |
|---|---|---|---|---|
| `Sentinel` (two products share the name) | A · ExactAlias | ambiguous · `hashicorp/sentinel` 0.3333, `microsoft/sentinel` 0.3333, `thales/sentinel` 0.3333 | raw 0.8 · margin 0.0 | ✅ |
| `Sentinel` (vendor=microsoft) (vendor hint) | A · ExactAlias | resolved `microsoft/sentinel` · 0.8 | raw 0.8 · +bonus → rank 0.95 · margin 0.15 | ✅ |
| `Sentinel` (filter vendors=hashicorp) (vendor filter) | A · ExactAlias | resolved `hashicorp/sentinel` · 0.8 | raw 0.8 · margin 0.8 | ✅ |
| `Sentinel SIEM` (context word in the input) | A · ExactAlias | resolved `microsoft/sentinel` · 0.9 | raw 0.9 · margin 0.9 | ✅ |
| `Falcon` (category=edr) (category hint) | A · ExactAlias | resolved `crowdstrike/falcon` · 0.8 | raw 0.8 · +bonus → rank 0.95 · margin 0.15 | ✅ |

## Paraphrases (semantic layer)

Vendor × concept phrases are compiled into aliases at build time; slang is rewritten at query time (D-49).

| Input | Matched at | Final answer | Why | Expected |
|---|---|---|---|---|
| `AWS managed Kubernetes` (build-time concept alias) | A · ExactAlias | resolved `aws/eks` · 0.8 | raw 0.8 · margin 0.8 | ✅ |
| `Fortinet firewall` (build-time concept alias) | A · ExactAlias | resolved `fortinet/fortigate` · 0.8 | raw 0.8 · margin 0.8 | ✅ |
| `Amazon managed k8` (k8 rewritten to kubernetes) | B · ExactAlias | resolved `aws/eks` · 0.8 | raw 0.8 · margin 0.8 | ✅ |
| `managed kubernetes` (no vendor: a concept alone is never an alias) | B · FuzzyAlias | ambiguous · `aws/eks` 0.5275, `google/kubernetes_engine` 0.4725 | raw 0.7673 · margin 0.08 | ✅ |

## Typos

Fuzzy matching fixes small misspellings, weighted by how rare each word is; words of 3 letters or fewer and ALL-CAPS acronyms are never corrected.

| Input | Matched at | Final answer | Why | Expected |
|---|---|---|---|---|
| `Crowdstrik Falcon` (vendor misspelled) | B · FuzzyAlias | resolved `crowdstrike/falcon` · 0.948 | raw 0.948 · margin 0.948 | ✅ |
| `Crowdstrike Falcn` (rank above 1, confidence stays raw) | B · FuzzyAlias | resolved `crowdstrike/falcon` · 0.904 | raw 0.904 · +bonus → rank 1.054 · margin 1.054 | ✅ |
| `Kubernets` (one word, one letter missing) | B · FuzzyAlias | resolved `kubernetes/kubernetes` · 0.8889 | raw 0.8889 · margin 0.3527 | ✅ |
| `Jira PAAS` (ALL-CAPS acronym kept as typed, not fixed to saas (D-50b)) | B · FuzzyAlias | no_match | best raw 0.4552 is below t_low 0.5 | ✅ |

## Must not resolve

Products outside the catalog stay unresolved even when they share words with known ones.

| Input | Matched at | Final answer | Why | Expected |
|---|---|---|---|---|
| `AWS Foo` (known vendor, unknown product) | — | no_match | no step found a candidate | ✅ |
| `Amazon Prime` (the vendor word alone is not enough) | B · FuzzyAlias | no_match | best raw 0.2835 is below t_low 0.5 | ✅ |
| `Microsoft 365` (not in the catalog) | — | no_match | no step found a candidate | ✅ |
| `Splunk Enterprise Security` (shares words with Splunk Enterprise) | B · FuzzyAlias | ambiguous · `splunk/enterprise` 1.0 | raw 0.6871 · +bonus → rank 0.8371 · margin 0.8371 | ✅ not resolved (gold: no_match) |
| `Acme Widget Pro` (nothing known) | — | no_match | no step found a candidate | ✅ |

## Known limits

Cases the resolver misses today, tracked in docs/GAPS.md.

| Input | Matched at | Final answer | Why | Expected |
|---|---|---|---|---|
| `AWS EKS cluster` (G-05: an extra generic word) | B · FuzzyAlias | ambiguous · `aws/eks` 1.0 | raw 0.5578 · +bonus → rank 0.7078 · margin 0.7078 | gap · want resolved `aws/eks` |
| `Crwdstrk Falcon` (more than 2 letters wrong) | B · FuzzyAlias | no_match | best raw 0.4226 is below t_low 0.5 | gap · want resolved `crowdstrike/falcon` |

## Appendix — optional (+5 minutes)

One full trace per group: the data each step read.

### Exact name or alias: `CrowdStrike Falcon`

Normalized: `crowdstrike falcon`

- **A · ExactAlias** on `crowdstrike falcon` → hit
  - alias `crowdstrike falcon` → `crowdstrike/falcon` (canonical, base 1.0)
- **Decide:** top `crowdstrike/falcon` raw 1.0 (≥ 0.75: yes), margin 1.0 (≥ 0.15: yes) → resolved `crowdstrike/falcon` · 1.0
- **Final answer:** resolved → crowdstrike/falcon (CrowdStrike Falcon), confidence 1.0. Confidence = raw 1.0 after calibration, capped at 1.0.

### Vendor names and prefixes: `MS`

Normalized: `ms`

- **A · ExactAlias** on `ms` → miss
- **A · JoinedWords** on `ms` → miss
- **A · CamelCaseSplit** on `ms` → miss
- **A · WithoutNumbers** on `ms` → miss
- **B · SynonymRewrite** on `ms` → no change
- **B · ExactAlias** on `ms` → miss
- **B · JoinedWords** on `ms` → miss
- **B · WithoutNumbers** on `ms` → miss
- **B · FuzzyAlias** on `ms` → hit
  - `microsoft/windows` via `ms os`: common ms 2.6892 = 2.6892 / union 6.054 = raw 0.4442
  - `microsoft/windows_server` via `ms os`: common ms 2.6892 = 2.6892 / union 6.054 = raw 0.4442
  - `microsoft/azure` via `ms cloud`: common ms 2.6892 = 2.6892 / union 6.1256 = raw 0.439

### Look-alikes kept apart: `C`

Normalized: `c`

- **A · ExactAlias** on `c` → hit
  - alias `c` → `c/c` (weak, base 0.8)
- **Decide:** top `c/c` raw 0.8 (≥ 0.75: yes), margin 0.8 (≥ 0.15: yes) → resolved `c/c` · 0.8
- **Final answer:** resolved → c/c (C), confidence 0.8. Confidence = raw 0.8 after calibration, capped at 1.0.

### Cleaning and retries: `Windows 10`

Normalized: `windows 10`

- **A · ExactAlias** on `windows 10` → miss
- **A · JoinedWords** on `windows 10` → miss
- **A · CamelCaseSplit** on `windows 10` → miss
- **A · WithoutNumbers** on `windows 10` → hit
  - alias `windows` → `microsoft/windows` (weak, base 0.8)
- **Decide:** top `microsoft/windows` raw 0.8 (≥ 0.75: yes), margin 0.8 (≥ 0.15: yes) → resolved `microsoft/windows` · 0.8
- **Final answer:** resolved → microsoft/windows (Microsoft Windows), confidence 0.8. Confidence = raw 0.8 after calibration, capped at 1.0.

### Same name, different products: `Sentinel`

Normalized: `sentinel`

- **A · ExactAlias** on `sentinel` → hit
  - alias `sentinel` → `hashicorp/sentinel` (weak, base 0.8)
  - alias `sentinel` → `microsoft/sentinel` (weak, base 0.8)
  - alias `sentinel` → `thales/sentinel` (weak, base 0.8)
- **Decide:** top `hashicorp/sentinel` raw 0.8 (≥ 0.75: yes), margin 0.0 (≥ 0.15: no) → ambiguous · `hashicorp/sentinel` 0.3333, `microsoft/sentinel` 0.3333, `thales/sentinel` 0.3333
- **Final answer:** ambiguous → the caller picks one of: hashicorp/sentinel 0.3333, microsoft/sentinel 0.3333, thales/sentinel 0.3333; confidence 0.8. Confidence = raw 0.8 after calibration, capped at 1.0; shares = each rank ÷ sum of shown ranks.

### Paraphrases (semantic layer): `managed kubernetes`

Normalized: `managed kubernetes`

- **A · ExactAlias** on `managed kubernetes` → miss
- **A · JoinedWords** on `managed kubernetes` → miss
- **A · CamelCaseSplit** on `managed kubernetes` → miss
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
- **Final answer:** ambiguous → the caller picks one of: aws/eks 0.5275, google/kubernetes_engine 0.4725; confidence 0.7673. Confidence = raw 0.7673 after calibration, capped at 1.0; shares = each rank ÷ sum of shown ranks.

### Typos: `Crowdstrik Falcon`

Normalized: `crowdstrik falcon`

- **A · ExactAlias** on `crowdstrik falcon` → miss
- **A · JoinedWords** on `crowdstrik falcon` → miss
- **A · CamelCaseSplit** on `crowdstrik falcon` → miss
- **A · WithoutNumbers** on `crowdstrik falcon` → miss
- **B · SynonymRewrite** on `crowdstrik falcon` → no change
- **B · ExactAlias** on `crowdstrik falcon` → miss
- **B · JoinedWords** on `crowdstrik falcon` → miss
- **B · WithoutNumbers** on `crowdstrik falcon` → miss
- **B · FuzzyAlias** on `crowdstrik falcon` → hit
  - `crowdstrike/falcon` via `crowdstrike falcon`: common crowdstrike 5.2807 + falcon 4.8777 = 9.6303 / union 10.1584 = raw 0.948
  - `falconry/falcon` via `falcon`: common falcon 4.8777 = 4.8777 / union 10.1584 = raw 0.4802
  - `crowdstrike/*` via `crowdstrike`: common crowdstrike 5.2807 = 4.7526 / union 10.1584 = raw 0.4678
- **Decide:** top `crowdstrike/falcon` raw 0.948 (≥ 0.75: yes), margin 0.948 (≥ 0.15: yes) → resolved `crowdstrike/falcon` · 0.948
- **Final answer:** resolved → crowdstrike/falcon (CrowdStrike Falcon), confidence 0.948. Confidence = raw 0.948 after calibration, capped at 1.0.

### Must not resolve: `Amazon Prime`

Normalized: `amazon prime`

- **A · ExactAlias** on `amazon prime` → miss
- **A · JoinedWords** on `amazon prime` → miss
- **A · CamelCaseSplit** on `amazon prime` → miss
- **A · WithoutNumbers** on `amazon prime` → miss
- **B · SynonymRewrite** on `amazon prime` → no change
- **B · ExactAlias** on `amazon prime` → miss
- **B · JoinedWords** on `amazon prime` → miss
- **B · WithoutNumbers** on `amazon prime` → miss
- **B · FuzzyAlias** on `amazon prime` → hit
  - `paloaltonetworks/prisma_cloud` via `prisma cloud`: common prisma 5.2807 = 3.1684 / union 11.1778 = raw 0.2835

### Known limits: `AWS EKS cluster`

Normalized: `aws eks cluster`

- **A · ExactAlias** on `aws eks cluster` → miss
- **A · JoinedWords** on `aws eks cluster` → miss
- **A · CamelCaseSplit** on `aws eks cluster` → miss
- **A · WithoutNumbers** on `aws eks cluster` → miss
- **B · SynonymRewrite** on `aws eks cluster` → no change
- **B · ExactAlias** on `aws eks cluster` → miss
- **B · JoinedWords** on `aws eks cluster` → miss
- **B · WithoutNumbers** on `aws eks cluster` → miss
- **B · FuzzyAlias** on `aws eks cluster` → hit
  - `aws/eks` via `aws eks`: common aws 3.1233 + eks 5.2807 = 8.404 / union 15.0671 = raw 0.5578
- **Decide:** top `aws/eks` raw 0.5578 (≥ 0.75: no), margin 0.7078 (≥ 0.15: yes) → ambiguous · `aws/eks` 1.0
- **Final answer:** ambiguous → the caller picks one of: aws/eks 1.0; confidence 0.5578. Confidence = raw 0.5578 after calibration, capped at 1.0; rank 0.7078 = raw 0.5578 + bonus only ordered the candidates; shares = each rank ÷ sum of shown ranks.
