const ANALYSIS_TYPES = [
  { label: "Raw Data", value: "raw" },
  { label: "Weighted Summary", value: "weighted" },
  { label: "Trends & Seasonality", value: "trends" },
];

const QUALITY_LEVELS = [
  { label: "All", value: "" },
  { label: "Excellent", value: "excellent" },
  { label: "Good", value: "good" },
  { label: "Questionable", value: "questionable" },
  { label: "Poor", value: "poor" },
];

function Filters({
  locations,
  metrics,
  filters,
  onFilterChange,
  onApplyFilters,
}) {
  const handleChange = (field, value) => {
    onFilterChange({
      ...filters,
      [field]: value,
    });
  };

  const handleDateChange = (field, value) => {
    handleChange(field, value);
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow-md">
      <h2 className="text-xl font-semibold text-eco-primary mb-4">
        Filter Data
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Location dropdown */}
        <div>
          <label className="block font-medium mb-1" htmlFor="location">
            Location
          </label>
          <select
            id="location"
            className="w-full border border-gray-300 rounded px-3 py-2"
            value={filters.locationId}
            onChange={(e) => handleChange("locationId", e.target.value)}
          >
            <option value="">All Locations</option>
            {locations.map((loc) => (
              <option key={loc.id} value={loc.id}>
                {loc.name} ({loc.country})
              </option>
            ))}
          </select>
        </div>

        {/* Metric dropdown */}
        <div>
          <label className="block font-medium mb-1" htmlFor="metric">
            Metric
          </label>
          <select
            id="metric"
            className="w-full border border-gray-300 rounded px-3 py-2"
            value={filters.metric}
            onChange={(e) => handleChange("metric", e.target.value)}
          >
            <option value="">All Metrics</option>
            {metrics.map((metric) => (
              <option key={metric.id} value={metric.name}>
                {metric.display_name || metric.name} ({metric.unit})
              </option>
            ))}
          </select>
        </div>

        {/* Analysis Type dropdown */}
        <div>
          <label className="block font-medium mb-1" htmlFor="analysisType">
            Analysis Type
          </label>
          <select
            id="analysisType"
            className="w-full border border-gray-300 rounded px-3 py-2"
            value={filters.analysisType}
            onChange={(e) => handleChange("analysisType", e.target.value)}
          >
            {ANALYSIS_TYPES.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Date Range */}
        <div>
          <label className="block font-medium mb-1" htmlFor="startDate">
            Start Date
          </label>
          <input
            id="startDate"
            type="date"
            className="w-full border border-gray-300 rounded px-3 py-2"
            value={filters.startDate}
            onChange={(e) => handleDateChange("startDate", e.target.value)}
            max={filters.endDate || undefined}
          />
        </div>
        <div>
          <label className="block font-medium mb-1" htmlFor="endDate">
            End Date
          </label>
          <input
            id="endDate"
            type="date"
            className="w-full border border-gray-300 rounded px-3 py-2"
            value={filters.endDate}
            onChange={(e) => handleDateChange("endDate", e.target.value)}
            min={filters.startDate || undefined}
          />
        </div>

        {/* Data Quality dropdown */}
        <div>
          <label className="block font-medium mb-1" htmlFor="quality">
            Data Quality
          </label>
          <select
            id="quality"
            className="w-full border border-gray-300 rounded px-3 py-2"
            value={filters.qualityThreshold}
            onChange={(e) => handleChange("qualityThreshold", e.target.value)}
          >
            {QUALITY_LEVELS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex flex-col md:flex-row md:items-center justify-between mt-4 gap-3">
        <button
          className="bg-eco-primary text-white font-semibold px-6 py-2 rounded hover:bg-eco-primary-dark shadow transition"
          onClick={onApplyFilters}
        >
          Apply Filters
        </button>
        <span className="text-gray-500 text-sm mt-2 md:mt-0">
          {Object.values(filters).filter((v) => v && v !== "raw").length > 0
            ? "Filters applied."
            : "No filters applied."}
        </span>
      </div>
    </div>
  );
}

export default Filters;
