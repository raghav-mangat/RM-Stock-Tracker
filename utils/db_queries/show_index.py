from models.database import db, Stock, Index, IndexHolding
from sqlalchemy import and_, or_

def get_index_data(index_id, sort_by, order, filter_by):
    valid_sort_by = {"weight", "name", "todays_change", "perc_diff"}
    valid_order = {"asc", "desc"}
    valid_filter = {"dark_green", "green", "yellow", "red", "dark_red"}

    # Normalize input
    if sort_by not in valid_sort_by:
        sort_by = None
    if order not in valid_order:
        order = None
    if not filter_by or not set(filter_by).issubset(valid_filter):
        filter_by = list(valid_filter)

    sort_dropdown_options = [
        {"label": "Weight (High to Low)", "sort_by": None, "order": None},
        {"label": "Weight (Low to High)", "sort_by": "weight", "order": "asc"},
        {"label": "Name (High to Low)", "sort_by": "name", "order": "desc"},
        {"label": "Name (Low to High)", "sort_by": "name", "order": "asc"},
        {"label": "Today's Change (High to Low)", "sort_by": "todays_change", "order": "desc"},
        {"label": "Today's Change (Low to High)", "sort_by": "todays_change", "order": "asc"},
        {"label": "200-DMA % Diff (High to Low)", "sort_by": "perc_diff", "order": "desc"},
        {"label": "200-DMA % Diff (Low to High)", "sort_by": "perc_diff", "order": "asc"},
    ]

    sort_options = {
        ("weight", "asc"): IndexHolding.weight.asc(),
        ("name", "desc"): Stock.name.desc(),
        ("name", "asc"): Stock.name.asc(),
        ("todays_change", "desc"): Stock.todays_change_perc.desc(),
        ("todays_change", "asc"): Stock.todays_change_perc.asc(),
        ("perc_diff", "desc"): Stock.dma_200_perc_diff.desc(),
        ("perc_diff", "asc"): Stock.dma_200_perc_diff.asc(),
    }

    # Build filtering conditions
    filter_conditions = []
    for color in filter_by:
        if color == "dark_green":
            filter_conditions.append(Stock.dma_200_perc_diff >= 10)
        elif color == "green":
            filter_conditions.append(and_(Stock.dma_200_perc_diff >= 2, Stock.dma_200_perc_diff < 10))
        elif color == "yellow":
            filter_conditions.append(and_(Stock.dma_200_perc_diff >= -2, Stock.dma_200_perc_diff < 2))
        elif color == "red":
            filter_conditions.append(and_(Stock.dma_200_perc_diff >= -10, Stock.dma_200_perc_diff < -2))
        elif color == "dark_red":
            filter_conditions.append(Stock.dma_200_perc_diff < -10)
    # Colour options and associated dummy values for the filter
    filter_colors = {
        "dark_green": 15,
        "green": 5,
        "yellow": 0,
        "red": -5,
        "dark_red": -15
    }

    # Fetch index
    index = Index.query.filter_by(slug=index_id).first_or_404()

    query = (
        db.session.query(
            IndexHolding.weight,
            Stock.ticker,
            Stock.name.label("stock_name"),
            Stock.day_close,
            Stock.low_52w,
            Stock.high_52w,
            Stock.todays_change_perc,
            Stock.todays_change,
            Stock.dma_200,
            Stock.dma_200_perc_diff
        )
        .join(Stock, IndexHolding.stock_id == Stock.id)
        .filter(IndexHolding.index_id == index.id)
    )

    # Only include NULLs if all filters are selected
    if set(filter_by) == valid_filter:
        query = query.filter(or_(*filter_conditions, Stock.dma_200_perc_diff.is_(None)))
    else:
        query = query.filter(or_(*filter_conditions))

    index_data = query.order_by(
        sort_options.get((sort_by, order), IndexHolding.weight.desc())
    ).all()

    result = {
        "index": index,
        "index_data": index_data,
        "sort_dropdown_options": sort_dropdown_options,
        "filter_colors": filter_colors
    }

    return result