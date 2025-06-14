def filter_candidates(user: dict, candidates: list) -> list:
    """
    Фильтрует и сортирует кандидатов по приблизительному совпадению навыков и виду деятельности.
    Показывает кандидатов противоположного seeking (если user ищет проект — показываем dev и наоборот).
    Исключает спящих и тех, кто в черном списке.
    """
    from collections import Counter

    user_skills = set(user.get("skills", []))
    user_activity = user.get("activity")
    user_id = user.get("id")
    seeking = user.get("seeking")
    blacklist = set(user.get("blacklist", []))
    is_sleeping = user.get("is_sleeping")

    if is_sleeping:
        return []

    filtered = []
    for c in candidates:
        if c["id"] == user_id:
            continue
        if c["id"] in blacklist:
            continue
        if c["is_sleeping"]:
            continue
        if c["seeking"] == seeking:
            continue

        skill_match = len(user_skills.intersection(set(c.get("skills", []))))
        activity_match = 1 if c.get("activity") == user_activity else 0
        score = skill_match * 2 + activity_match

        filtered.append((score, c))

    filtered.sort(key=lambda x: x[0], reverse=True)
    return [c[1] for c in filtered if c[0] > 0]
