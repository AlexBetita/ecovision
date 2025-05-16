# app.py - EcoVision: Climate Visualizer API
import os
import statistics

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, List, Any
from datetime import date, datetime
from dotenv import load_dotenv

from db import database, create_schema, seed_data_from_file, drop_tables

load_dotenv() 

# Database connection
DATABASE_URL = f"mysql://{os.environ.get('MYSQL_USER', 'root')}:{os.environ.get('MYSQL_PASSWORD', '')}@{os.environ.get('MYSQL_HOST', 'localhost')}/{os.environ.get('MYSQL_DB', 'climate_data')}"

app = FastAPI(title="EcoVision API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await database.connect()
    # await drop_tables()
    await create_schema()
    await seed_data_from_file()
    

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# GLOBALS
QUALITY_WEIGHTS = {
    "excellent": 1.0,
    "good": 0.8,
    "questionable": 0.5,
    "poor": 0.3,
}

SEASONS = {
    "winter": [12, 1, 2],
    "spring": [3, 4, 5],
    "summer": [6, 7, 8],
    "fall":   [9, 10, 11],
}

@app.get("/api/v1/climate")
async def get_climate_data(
    location_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    metric: Optional[str] = Query(None),
    quality_threshold: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    # Build filters
    clauses, vals = [], {}
    if location_id:
        clauses.append("c.location_id = :location_id")
        vals["location_id"] = location_id
    if start_date:
        clauses.append("c.date >= :start_date")
        vals["start_date"] = start_date.isoformat()
    if end_date:
        clauses.append("c.date <= :end_date")
        vals["end_date"] = end_date.isoformat()
    if metric:
        clauses.append("m.name = :metric")
        vals["metric"] = metric
    if quality_threshold:
        clauses.append("c.quality = :quality_threshold")
        vals["quality_threshold"] = quality_threshold

    where = " AND ".join(clauses) if clauses else "1=1"

    # Include offset and limit
    offset = (page - 1) * per_page
    data_q = f"""
    SELECT
      c.id,
      c.location_id,
      l.name       AS location_name,
      l.latitude,
      l.longitude,
      c.date,
      m.name       AS metric,
      c.value,
      m.unit,
      c.quality
    FROM climate_measurements c
    JOIN locations l ON c.location_id = l.id
    JOIN metrics   m ON c.metric_id   = m.id
    WHERE {where}
    ORDER BY c.date
    LIMIT {per_page}
    OFFSET {offset}
    """
    rows = await database.fetch_all(data_q, vals)

    # count total
    cnt_q = f"""
    SELECT COUNT(*) AS total
    FROM climate_measurements c
    JOIN locations l ON c.location_id = l.id
    JOIN metrics   m ON c.metric_id   = m.id
    WHERE {where}
    """
    cnt = await database.fetch_one(cnt_q, vals)
    total = cnt["total"] or 0

    # not a great solution for stripping the time off the date. better to use pydantic models
    # when defining the schema as it will know what to serialize

    data = []
    for r in rows:
        rec = dict(r)
        # if it's a datetime, use .date(), otherwise assume date
        rec["date"] = (
            rec["date"].date().isoformat()
            if hasattr(rec["date"], "date")
            else rec["date"].isoformat()
        )
        data.append(rec)

    return {
        "data": data,
        "meta": {"total_count": total, "page": page, "per_page": per_page},
    }

@app.get("/api/v1/locations")
async def get_locations():
    rows = await database.fetch_all(
        "SELECT id, name, country, latitude, longitude FROM locations"
    )
    return {"data": [dict(r) for r in rows]}

@app.get("/api/v1/metrics")
async def get_metrics():
    rows = await database.fetch_all(
        "SELECT id, name, display_name, unit, description FROM metrics"
    )
    return {"data": [dict(r) for r in rows]}

@app.get("/api/v1/summary")
async def get_summary(
    location_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    metric: Optional[str] = Query(None),
    quality_threshold: Optional[str] = Query(None),
):
    # filter out the data
    clauses, vals = [], {}
    if location_id:
        clauses.append("c.location_id = :location_id"); vals["location_id"] = location_id
    if start_date:
        clauses.append("c.date >= :start_date");    vals["start_date"] = start_date.isoformat()
    if end_date:
        clauses.append("c.date <= :end_date");      vals["end_date"] = end_date.isoformat()
    if metric:
        clauses.append("m.name = :metric");         vals["metric"] = metric
    if quality_threshold:
        clauses.append("c.quality = :quality_threshold"); vals["quality_threshold"] = quality_threshold
    where = " AND ".join(clauses) if clauses else "1=1"

    q = f"""
    SELECT
      m.name   AS metric,
      c.value  AS value,
      c.quality,
      m.unit   AS unit
    FROM climate_measurements c
    JOIN metrics m ON c.metric_id = m.id
    WHERE {where}
    """
    rows = await database.fetch_all(q, vals)
    if not rows:
        return {"data": {}}

    # Aggregate in Python
    buckets: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        name = r["metric"]
        v = r["value"]
        ql = r["quality"]
        w = QUALITY_WEIGHTS.get(ql, 0)
        b = buckets.setdefault(name, {
            "values": [], "weight_sum": 0.0, "weight_factor_sum": 0.0, "qualities": [], "unit": r["unit"]
        })
        b["values"].append(v)
        b["weight_sum"] += v * w
        b["weight_factor_sum"] += w
        b["qualities"].append(ql)

    out = {}
    for name, b in buckets.items():
        vals_list = b["values"]
        qs = b["qualities"]
        cnt = len(vals_list)
        dist = {q: qs.count(q) / cnt for q in set(qs)}
        weighted_avg = b["weight_sum"] / b["weight_factor_sum"] if b["weight_factor_sum"] else None

        out[name] = {
            "min": min(vals_list),
            "max": max(vals_list),
            "avg": statistics.mean(vals_list),
            "weighted_avg": weighted_avg,
            "unit": b["unit"],
            "quality_distribution": dist,
        }

    return {"data": out}

@app.get("/api/v1/trends")
async def get_trends(
    location_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    metric: Optional[str] = Query(None),
    quality_threshold: Optional[str] = Query(None),
):
    # filter data
    clauses, vals = [], {}
    if location_id:
        clauses.append("c.location_id = :location_id"); vals["location_id"] = location_id
    if start_date:
        clauses.append("c.date >= :start_date");    vals["start_date"] = start_date.isoformat()
    if end_date:
        clauses.append("c.date <= :end_date");      vals["end_date"] = end_date.isoformat()
    if metric:
        clauses.append("m.name = :metric");         vals["metric"] = metric
    if quality_threshold:
        clauses.append("c.quality = :quality_threshold"); vals["quality_threshold"] = quality_threshold
    where = " AND ".join(clauses) if clauses else "1=1"

    q = f"""
    SELECT
      m.name     AS metric,
      c.date     AS date,
      c.value    AS value,
      c.quality  AS quality
    FROM climate_measurements c
    JOIN metrics m ON c.metric_id = m.id
    WHERE {where}
    ORDER BY c.date
    """
    rows = await database.fetch_all(q, vals)
    if not rows:
        return {"data": {}}

    # Group by metric
    series: Dict[str, List[Dict[str,Any]]] = {}
    for r in rows:
        series.setdefault(r["metric"], []).append({
            "date":    r["date"],
            "value":   r["value"],
            "quality": r["quality"],
        })

    result: Dict[str, Any] = {}
    for mname, pts in series.items():
        # Sort by date
        pts.sort(key=lambda x: x["date"])
        dates = [p["date"] for p in pts]
        vals_ = [p["value"] for p in pts]

        # calcualte trend
        first, last = vals_[0], vals_[-1]
        days = (dates[-1] - dates[0]).days or 1
        rate = ((last - first) / days) * 30
        direction = "increasing" if rate > 0 else "decreasing" if rate < 0 else "stable"
        trend = {
            "direction":  direction,
            "rate":       round(rate, 1),
            "unit":       "per month",
            "confidence": 0.9,
        }

        # calculate the Anomalies
        u = statistics.mean(vals_)
        o = statistics.stdev(vals_) if len(vals_) > 1 else 0
        anomalies = []
        if o:
            for p in pts:
                dev = abs(p["value"] - u)
                if dev > 2 * o:
                    d = p["date"]
                    anomalies.append({
                        "date":      d.date().isoformat() if isinstance(d, datetime) else d.isoformat(),
                        "value":     p["value"],
                        "deviation": round(dev/o, 1),
                        "quality":   p["quality"],
                    })

        # calculate the seasons
        season_stats = {}
        seasons_with_data = 0
        for season, months in SEASONS.items():
            # collect points for this season
            sp = [p for p in pts if p["date"].month in months]
            if len(sp) >= 2:
                seasons_with_data += 1
                vals_s = [p["value"] for p in sp]
                dates_s = [p["date"] for p in sp]
                avg_s = round(statistics.mean(vals_s), 1)
                # simple trend: first→last in that season
                days_s = (dates_s[-1] - dates_s[0]).days or 1
                rate_s = ((vals_s[-1] - vals_s[0]) / days_s) * 30
                dir_s = "increasing" if rate_s > 0 else "decreasing" if rate_s < 0 else "stable"
                season_stats[season] = {"avg": avg_s, "trend": dir_s}
            else:
                # no or single point: default
                season_stats[season] = {"avg": 0.0, "trend": "stable"}

        detected = seasons_with_data >= 2
        confidence = round(seasons_with_data / 4, 2)

        seasonality = {
            "detected":   detected,
            "period":     "yearly",
            "confidence": confidence,
            "pattern":    season_stats,
        }

        result[mname] = {
            "trend":       trend,
            "anomalies":   anomalies,
            "seasonality": seasonality,
        }

    return {"data": result}