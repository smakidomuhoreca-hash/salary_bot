WORKERS = [
    # ── Виробництво (9 зл/кг) ──────────────────────────────────────────
    {
        "name": "Ольга М.",
        "type": "kg",
        "fixed_extra": 500,
        "bonus": 0,
    },
    {
        "name": "Валентина З.",
        "type": "kg",
        "fixed_extra": 0,
        "bonus": 0,
    },
    {
        "name": "Галина П.",
        "type": "kg",
        "fixed_extra": 0,
        "bonus": 0,
    },
    {
        "name": "Олена Л.",
        "type": "kg",
        "fixed_extra": 0,
        "bonus": 0,
    },
    {
        "name": "Маргарита К.",
        "type": "kg",
        "fixed_extra": 0,
        "bonus": 0,
    },
    {
        "name": "Віталіна З.",
        "type": "kg",
        "fixed_extra": 0,
        "bonus": 0,
    },

    # ── Продажі ────────────────────────────────────────────────────────
    {
        "name": "Мар'яна В.",
        "type": "sales",
        "rate": 22,
        "multi_point": True,   # вибирає точку щодня
        "threshold": None,     # threshold визначається динамічно по точці
        "bonus": 60,
        "fixed_extra": 0,
    },
    {
        "name": "Діана М.",
        "type": "sales",
        "rate": 22,
        "multi_point": False,
        "point": "A",
        "threshold": 5000,
        "bonus": 120,
        "fixed_extra": 0,
    },
    {
        "name": "Інна Ш.",
        "type": "sales",
        "rate": 25,
        "multi_point": False,
        "point": "C",
        "threshold": None,     # немає відсотку
        "bonus": 0,
        "fixed_extra": 0,
    },
    {
        "name": "Ангеліна П.",
        "type": "sales",
        "rate": 22,
        "multi_point": False,
        "point": "B",
        "threshold": 2000,
        "bonus": 0,
        "fixed_extra": 0,
    },
]
