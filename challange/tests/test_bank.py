import sys

import pytest

pytest.importorskip("src.resolver")

from src.constants import Status  # noqa: E402
from src.models import Hints, Resolution  # noqa: E402
from src.resolver import Resolver  # noqa: E402

BANK_SIZE = 25
bank = pytest.mark.bank


def _ids(resolver: Resolver, *names: str) -> set[str | None]:
    return {resolver.resolve(name).id for name in names}


@bank("AWS → AWS (cloud platform)")
def test_bank_01_aws_is_cloud_platform(resolver: Resolver) -> None:
    result = resolver.resolve("AWS")
    assert (result.id, result.category, result.status) == ("aws/aws", "cloud-platform", Status.RESOLVED)


@bank("Amazon Web Services / AWS Cloud → AWS")
def test_bank_02_aws_aliases_converge(resolver: Resolver) -> None:
    assert _ids(resolver, "AWS", "Amazon Web Services", "AWS Cloud") == {"aws/aws"}


@bank("AWS EKS / Amazon EKS / Amazon Elastic Kubernetes Service → AWS EKS")
def test_bank_03_eks_aliases_converge(resolver: Resolver) -> None:
    names = ("AWS EKS", "Amazon EKS", "Amazon Elastic Kubernetes Service")
    assert _ids(resolver, *names) == {"aws/eks"}
    assert resolver.resolve("Amazon EKS").canonical_name == "AWS EKS"


@bank("EKS → AWS EKS, lower confidence")
def test_bank_04_weak_unique_alias(resolver: Resolver) -> None:
    weak, full = resolver.resolve("EKS"), resolver.resolve("AWS EKS")
    assert (weak.id, weak.status) == ("aws/eks", Status.RESOLVED)
    assert weak.confidence < full.confidence


@bank("Amazon Web Services vs AWS EKS → different ids")
def test_bank_05_parent_platform_is_not_child(resolver: Resolver) -> None:
    assert resolver.resolve("Amazon Web Services").id != resolver.resolve("AWS EKS").id


@bank("Amazon vs AWS → different ids")
def test_bank_06_amazon_is_not_aws(resolver: Resolver) -> None:
    amazon = resolver.resolve("Amazon")
    assert amazon.id == "amazon/*"
    assert amazon.id != resolver.resolve("AWS").id


@bank("AWS Foo → no_match")
def test_bank_07_unknown_residue_never_falls_back(resolver: Resolver) -> None:
    result = resolver.resolve("AWS Foo")
    assert (result.status, result.canonical_name, result.confidence) == (Status.NO_MATCH, None, 0)


@bank("Sentinel → ambiguous + alternatives")
def test_bank_08_sentinel_is_ambiguous(resolver: Resolver) -> None:
    result = resolver.resolve("Sentinel")
    assert result.status is Status.AMBIGUOUS
    assert {alt.id for alt in result.alternatives} >= {"microsoft/sentinel", "hashicorp/sentinel", "thales/sentinel"}


@bank("Microsoft Sentinel / Azure Sentinel → Microsoft Sentinel")
def test_bank_09_microsoft_sentinel(resolver: Resolver) -> None:
    assert _ids(resolver, "Microsoft Sentinel", "Azure Sentinel") == {"microsoft/sentinel"}
    assert resolver.resolve("Azure Sentinel").canonical_name == "Microsoft Sentinel"


@bank("Sentinel SIEM → Microsoft Sentinel")
def test_bank_10_category_keyword_decides(resolver: Resolver) -> None:
    result = resolver.resolve("Sentinel SIEM")
    assert (result.id, result.status) == ("microsoft/sentinel", Status.RESOLVED)


@bank("SentinelOne → SentinelOne")
def test_bank_11_sentinelone_is_not_sentinel(resolver: Resolver) -> None:
    assert resolver.resolve("SentinelOne").id == "sentinelone/sentinelone"


@bank("CrowdStrike Falcon / Falcon EDR → CrowdStrike Falcon")
def test_bank_12_vendor_or_category_narrows(resolver: Resolver) -> None:
    assert _ids(resolver, "CrowdStrike Falcon", "Falcon EDR") == {"crowdstrike/falcon"}
    assert resolver.resolve("Falcon").status is Status.AMBIGUOUS


@bank("Crowdstrik Falcon → CrowdStrike Falcon, lower confidence")
def test_bank_13_typo_lower_confidence(resolver: Resolver) -> None:
    typo, exact = resolver.resolve("Crowdstrik Falcon"), resolver.resolve("CrowdStrike Falcon")
    assert (typo.id, typo.status) == ("crowdstrike/falcon", Status.RESOLVED)
    assert typo.confidence < exact.confidence


@bank("Microsoft → vendor Microsoft")
def test_bank_14_vendor_only_input(resolver: Resolver) -> None:
    result = resolver.resolve("Microsoft")
    assert (result.id, result.category) == ("microsoft/*", "vendor")


@bank("Microsoft Copilot vs GitHub Copilot → different ids")
def test_bank_15_own_product_beats_subsidiary(resolver: Resolver) -> None:
    assert resolver.resolve("Microsoft Copilot").id == "microsoft/copilot"
    assert resolver.resolve("GitHub Copilot").id == "github/copilot"


@bank("Nginx / F5 NGINX → Nginx (vendor F5)")
def test_bank_16_sub_vendor(resolver: Resolver) -> None:
    assert _ids(resolver, "Nginx", "F5 NGINX") == {"nginx/nginx"}
    assert resolver.resolve("F5 NGINX").canonical_name == "Nginx"


@bank("log4j / Log4j2 / Apache Log4j 2.14 → Apache Log4j")
def test_bank_17_version_stripped(resolver: Resolver) -> None:
    assert _ids(resolver, "log4j", "Log4j2", "Apache Log4j 2.14") == {"apache/log4j"}
    assert resolver.resolve("Apache Log4j 2.14").canonical_name == "Apache Log4j"


@bank("Experience Manager (AEM) Forms → Adobe Experience Manager Forms")
def test_bank_18_parenthetical_acronym(resolver: Resolver) -> None:
    result = resolver.resolve("Experience Manager (AEM) Forms")
    assert result.canonical_name == "Adobe Experience Manager Forms"


@bank("Acrobat and Reader → ambiguous / no_match")
def test_bank_19_compound_name(resolver: Resolver) -> None:
    assert resolver.resolve("Acrobat and Reader").status in {Status.AMBIGUOUS, Status.NO_MATCH}


@bank("Google Cloud vs Google → different ids")
def test_bank_20_noise_word_kept(resolver: Resolver) -> None:
    assert resolver.resolve("Google Cloud").id == "google/cloud"
    assert resolver.resolve("Google").id == "google/*"


@bank("C++ vs C# vs C → different ids")
def test_bank_21_symbol_table(resolver: Resolver) -> None:
    assert [resolver.resolve(name).id for name in ("C++", "C#", "C")] == ["cpp/cpp", "csharp/csharp", "c/c"]


@bank("k8s → Kubernetes")
def test_bank_22_k8s(resolver: Resolver) -> None:
    assert resolver.resolve("k8s").canonical_name == "Kubernetes"


@bank("VS Code → Microsoft Visual Studio Code")
def test_bank_23_vs_code(resolver: Resolver) -> None:
    assert resolver.resolve("VS Code").canonical_name == "Microsoft Visual Studio Code"


@bank("Atlassian SourceTree → Atlassian Sourcetree")
def test_bank_24_casing(resolver: Resolver) -> None:
    assert resolver.resolve("Atlassian SourceTree").canonical_name == "Atlassian Sourcetree"


@bank("any input twice → same output + same index_version")
def test_bank_25_idempotent(resolver: Resolver) -> None:
    first: Resolution = resolver.resolve("AWS EKS", hints=Hints())
    assert resolver.resolve("AWS EKS", hints=Hints()) == first


def test_bank_has_25_cases() -> None:
    module = sys.modules[__name__]
    cases = [name for name in dir(module) if name.startswith("test_bank_") and name[10:12].isdigit()]
    assert len(cases) == BANK_SIZE
