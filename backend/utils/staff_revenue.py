"""Helpers for computing per-staff revenue attribution from bills.

Per-staff revenue is allocated proportionally from each bill's `final_amount`
(the cash actually collected), so that the sum of all per-staff revenues equals
the cash register's bill-sourced "total in" for the same period & branch.

For each bill:
    gross = sum(items.total)
    item.attributed_revenue = (item.total / gross) * bill.final_amount   if gross > 0
                            = bill.final_amount / item_count             if gross == 0 (rare)
                            = 0                                          if final_amount == 0

This handles bill-level discounts (manual or membership), tax, referral
discounts, and inclusive-pricing edge cases — all of which previously caused
staff-performance reports to disagree with the cash register.
"""


def attributed_revenue_pipeline(match_stage):
    """Return MongoDB pipeline stages that explode bill items and attach
    `_attributed_revenue` to each unwound item.

    Caller appends grouping / lookup / projection stages after these.
    """
    return [
        {"$match": match_stage},
        {"$addFields": {
            "_gross": {"$sum": "$items.total"},
            "_item_count": {"$size": {"$ifNull": ["$items", []]}},
        }},
        {"$unwind": "$items"},
        {"$addFields": {
            "_attributed_revenue": {
                "$cond": [
                    {"$gt": ["$_gross", 0]},
                    {"$multiply": [
                        {"$divide": [{"$ifNull": ["$items.total", 0]}, "$_gross"]},
                        {"$ifNull": ["$final_amount", 0]},
                    ]},
                    {"$cond": [
                        {"$gt": ["$_item_count", 0]},
                        {"$divide": [
                            {"$ifNull": ["$final_amount", 0]},
                            "$_item_count",
                        ]},
                        0,
                    ]},
                ]
            }
        }},
    ]
