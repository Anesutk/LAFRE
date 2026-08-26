"""
Hardcoded public-safety and healthcare service data for the prototype.

Later replacement path:
1. Create a LocalService Django model.
2. Move this list into database rows.
3. Keep the same recommend_local_services() tool response shape.
"""

GENERAL_EMERGENCY = {
    "label": "General emergency number",
    "phone": "112",
    "note": "Use for urgent ambulance, fire, or police assistance where available.",
}

LOCAL_SERVICES = [
    {
        "city": "Harare",
        "type": "police",
        "name": "Harare Central Police Station",
        "phone": "+263 242 777777",
        "address": "Harare CBD",
        "note": "Prototype record. Confirm exact contact details before production use.",
    },
    {
        "city": "Bulawayo",
        "type": "police",
        "name": "Bulawayo Central Police Station",
        "phone": "+263 292 72515",
        "address": "Bulawayo CBD",
        "note": "Prototype record. Confirm exact contact details before production use.",
    },
    {
        "city": "Gweru",
        "type": "police",
        "name": "Gweru Central Police Station",
        "phone": "To be updated",
        "address": "Gweru CBD",
        "note": "Prototype record. Replace with verified database value later.",
    },
    {
        "city": "Mutare",
        "type": "police",
        "name": "Mutare Central Police Station",
        "phone": "To be updated",
        "address": "Mutare CBD",
        "note": "Prototype record. Replace with verified database value later.",
    },
    {
        "city": "Masvingo",
        "type": "police",
        "name": "Masvingo Central Police Station",
        "phone": "To be updated",
        "address": "Masvingo CBD",
        "note": "Prototype record. Replace with verified database value later.",
    },
    {
        "city": "Harare",
        "type": "healthcare",
        "name": "Nearest hospital or clinic",
        "phone": "112",
        "address": "Use the nearest safe health facility",
        "note": "For injury, assault, poisoning, or serious distress, seek medical help quickly.",
    },
    {
        "city": "Bulawayo",
        "type": "healthcare",
        "name": "Nearest hospital or clinic",
        "phone": "112",
        "address": "Use the nearest safe health facility",
        "note": "For injury, assault, poisoning, or serious distress, seek medical help quickly.",
    },
    {
        "city": "Gweru",
        "type": "healthcare",
        "name": "Nearest hospital or clinic",
        "phone": "112",
        "address": "Use the nearest safe health facility",
        "note": "For injury, assault, poisoning, or serious distress, seek medical help quickly.",
    },
]


def find_services(city="", service_type=""):
    city = (city or "").strip().lower()
    service_type = (service_type or "").strip().lower()
    rows = LOCAL_SERVICES
    if service_type:
        rows = [row for row in rows if row["type"] == service_type]
    if city:
        exact = [row for row in rows if row["city"].lower() == city]
        if exact:
            return exact
    return rows[:4]
