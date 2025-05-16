import os
import json

from databases import Database
from pathlib import Path

# DATABASE URL from env or defaults
DATABASE_URL = (
    f"mysql://{os.getenv('MYSQL_USER','root')}"
    f":{os.getenv('MYSQL_PASSWORD','')}"
    f"@{os.getenv('MYSQL_HOST','localhost')}"
    f"/{os.getenv('MYSQL_DB','climate_data')}"
)

# single Database instance for the whole app/singleton pattern
database = Database(DATABASE_URL)

async def create_schema():
    # locations table
    # longest country name is The United Kingdom of Great Britain and Northern Ireland -> 28 characters long
    await database.execute(
        """
        CREATE TABLE IF NOT EXISTS locations (
          id         INT AUTO_INCREMENT PRIMARY KEY,
          name       VARCHAR(255) NOT NULL,
          country    VARCHAR(28) NOT NULL,
          region     VARCHAR(255),
          latitude   DOUBLE NOT NULL,
          longitude  DOUBLE NOT NULL
        );
        """
    )

    # metrics table
    # we use enum here for storage efficiency, data validation, performance and consistency
    # also allows for flexibility
    # min and max value to prevent certain values from going through when in relationship with climate data
    await database.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            name          ENUM('temperature','precipitation','humidity') NOT NULL,
            display_name  VARCHAR(100)
            AS (
                CONCAT(
                UPPER(LEFT(name,1)),
                LOWER(SUBSTRING(name,2))
                )
            )
            STORED,
            unit          ENUM('celsius','mm','percent')   NOT NULL,
            description   VARCHAR(255),
            min_value     DOUBLE NOT NULL COMMENT 'absolute minimum acceptable',
            max_value     DOUBLE NOT NULL COMMENT 'absolute maximum acceptable'
        );
    """)

    # add ranges for our metrics to prevent anomalies
    # create the seed data for metrics
    await database.execute("""
        INSERT INTO metrics (id, name, unit, description, min_value, max_value)
        VALUES
          (1, 'temperature', 'celsius', 'Average daily temperature', -10, 40),
          (2, 'precipitation','mm',      'Daily precipitation amount',   0,  40),
          (3, 'humidity',    'percent', 'Average daily humidity',         0, 100)
        AS new_metrics (id, name, unit, description, min_value, max_value)
        ON DUPLICATE KEY UPDATE
          min_value = new_metrics.min_value,
          max_value = new_metrics.max_value;
    """)

    # climate_measurements table
    await database.execute(
        """
        CREATE TABLE IF NOT EXISTS climate_measurements (
          id          INT AUTO_INCREMENT PRIMARY KEY,
          date        DATETIME     NOT NULL,
          value       DOUBLE       NOT NULL,
          quality     ENUM('poor','questionable', 'good', 'excellent') NOT NULL,
          location_id INT          NOT NULL,
          metric_id   INT          NOT NULL,
          FOREIGN KEY (location_id) REFERENCES locations(id),
          FOREIGN KEY (metric_id)   REFERENCES metrics(id)
        );
        """
    )

    # drop existing trigger if it exists (to allow rerunning)
    # enforcing data integrity and making the schema setup idempotent
    await database.execute("DROP TRIGGER IF EXISTS trg_check_value_range;")

    await database.execute("""
    CREATE TRIGGER trg_check_value_range
    BEFORE INSERT ON climate_measurements
    FOR EACH ROW
    BEGIN
      DECLARE v_min DOUBLE;
      DECLARE v_max DOUBLE;

      -- pull the allowed range for this metric
      SELECT min_value, max_value
        INTO v_min, v_max
        FROM metrics
       WHERE id = NEW.metric_id;

      -- if outside [min,max], abort with a static message
      IF NEW.value < v_min OR NEW.value > v_max THEN
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Measurement value out of allowed range';
      END IF;
    END;
    """)

async def seed_data_from_file():
    # load JSON
    base = Path(__file__).resolve().parent
    data = json.loads((base.parent / "data" / "sample_data.json").read_text())

    # we just upsert the data to prevent dupes and update the existing seeds 
    # if we decide to change the sample data

    # locations
    await database.execute_many(
        """
        INSERT INTO locations (id, name, country, latitude, longitude, region)
        VALUES (:id, :name, :country, :latitude, :longitude, :region)
        AS locations_data(id, name, country, latitude, longitude, region)
        ON DUPLICATE KEY UPDATE
          name     = locations_data.name,
          country  = locations_data.country,
          latitude = locations_data.latitude,
          longitude= locations_data.longitude,
          region   = locations_data.region
        """,
        data["locations"],
    )

    # climate measurements
    for row in data["climate_data"]:
        try:
            await database.execute(
                """
                INSERT INTO climate_measurements
                  (id, date, value, quality, location_id, metric_id)
                VALUES
                  (:id, :date, :value, :quality, :location_id, :metric_id)
                AS climate_measurements_data(id, date, value, quality, location_id, metric_id)
                ON DUPLICATE KEY UPDATE
                  date        = climate_measurements_data.date,
                  value       = climate_measurements_data.value,
                  quality     = climate_measurements_data.quality,
                  location_id = climate_measurements_data.location_id,
                  metric_id   = climate_measurements_data.metric_id
                """,
                row,
            )
        except Exception as e:
            # skip any row that errors (out-of-range or otherwise)
            print(f"⚠️  Skipped measurement {row.get('id')} due to metric value error.")
            continue


async def drop_tables():
    await database.execute("DROP TRIGGER IF EXISTS trg_check_value_range;")
    await database.execute("DROP TABLE IF EXISTS climate_measurements;")
    await database.execute("DROP TABLE IF EXISTS metrics;")
    await database.execute("DROP TABLE IF EXISTS locations;")