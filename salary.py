def calculate_salary(worker: dict, kg: float = None, hours: float = None,
                     sales: float = None, threshold: int = None) -> dict:
    result = {"base": 0.0, "percent": 0.0, "bonus": 0.0, "fixed_extra": 0.0, "total": 0.0}

    if worker["type"] == "kg":
        kg = kg or 0
        result["kg"] = kg
        result["base"] = round(kg * 9, 2)
        result["fixed_extra"] = worker.get("fixed_extra", 0)
        result["bonus"] = worker.get("bonus", 0)

    elif worker["type"] == "sales":
        hours = hours or 0
        result["hours"] = hours
        result["base"] = round(hours * worker["rate"], 2)

        thr = threshold if threshold is not None else worker.get("threshold")
        if thr and sales and sales > thr:
            result["percent"] = round((sales - thr) * 0.02, 2)

        result["bonus"] = worker.get("bonus", 0)
        result["fixed_extra"] = worker.get("fixed_extra", 0)

    result["total"] = round(
        result["base"] + result["percent"] + result["bonus"] + result["fixed_extra"], 2
    )
    return result
