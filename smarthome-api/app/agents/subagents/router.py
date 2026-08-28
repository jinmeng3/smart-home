DOMAIN_KEYWORDS: dict[str, set[str]] = {
    "device": {"设备", "灯", "空调", "温度", "离线", "告警", "状态", "插座", "开关"},
    "scene": {"场景", "模式", "回家", "离家", "观影", "睡眠", "起床"},
    "automation": {"自动化", "定时", "每天", "每周", "如果", "当", "触发", "规则"},
    "energy": {"能耗", "用电", "费电", "电量", "节能", "电费", "功率", "账单"},
    "comfort": {"舒适", "舒适度", "湿度", "通风", "太热", "太冷", "太干"},
    "security": {
        "门锁",
        "摄像头",
        "安防",
        "警报",
        "监控",
        "布防",
        "撤防",
        "入侵",
        "锁",
        "门铃",
        "报警",
    },
}

# 声明顺序即路由优先级；多命中时按此顺序返回。
_ORDERED_DOMAINS: tuple[str, ...] = tuple(DOMAIN_KEYWORDS)

# 可委托给只读子 Agent 的领域。device / security 具备可用的只读工具集；
# energy / comfort 待补齐工具后再加入。
DELEGATABLE_READ_ONLY_DOMAINS: frozenset[str] = frozenset({"device", "security"})

# 写能力域：委托给子 Agent 后，写操作仍会走 risk_check → approval 审批链路。
DELEGATABLE_WRITE_DOMAINS: frozenset[str] = frozenset({"automation", "scene"})

DELEGATABLE_DOMAINS: frozenset[str] = (
    DELEGATABLE_READ_ONLY_DOMAINS | DELEGATABLE_WRITE_DOMAINS
)


def route_intent(message: str) -> list[str]:
    """规则层路由，返回命中的领域标签列表（支持复合意图）。

    未命中任何领域时返回 ``["general"]``。
    """
    if not message:
        return ["general"]

    lowered = message.lower()
    tags = [
        domain
        for domain in _ORDERED_DOMAINS
        if any(keyword in lowered for keyword in DOMAIN_KEYWORDS[domain])
    ]
    return tags or ["general"]


def resolve_delegated_domain(message: str) -> str | None:
    """决定是否把请求委托给领域子 Agent。"""
    tags = route_intent(message)
    if len(tags) == 1 and tags[0] in DELEGATABLE_DOMAINS:
        return tags[0]
    return None


def is_write_domain(domain: str | None) -> bool:
    """是否为需要走写审批链路的委托领域。"""
    return domain in DELEGATABLE_WRITE_DOMAINS
