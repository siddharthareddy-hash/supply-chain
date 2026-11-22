INSERT INTO Dim_Date (Date_Key, Full_Date, Year, Quarter, Month, Month_Name, Week_Of_Year, Day_Of_Week, Is_Weekend, Is_Holiday)
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INT,
    d::DATE,
    EXTRACT(YEAR FROM d)::INT,
    EXTRACT(QUARTER FROM d)::INT,
    EXTRACT(MONTH FROM d)::INT,
    TO_CHAR(d, 'Month'),
    EXTRACT(WEEK FROM d)::INT,
    EXTRACT(ISODOW FROM d)::INT,
    EXTRACT(ISODOW FROM d) IN (6, 7),
    FALSE
FROM generate_series(DATE '2024-01-01', DATE '2025-12-31', INTERVAL '1 day') AS d
ON CONFLICT (Date_Key) DO NOTHING;
INSERT INTO Dim_Warehouse (Warehouse_ID, Warehouse_Name, City, Country, Region, Latitude, Longitude)
VALUES
    ('WH-01', 'Rotterdam DC',    'Rotterdam',   'Netherlands',  'EMEA', 51.924420, 4.477730),
    ('WH-02', 'Singapore Hub',   'Singapore',   'Singapore',    'APAC',  1.290270, 103.851959),
    ('WH-03', 'LA Distribution', 'Los Angeles', 'United States','AMER', 34.052234, -118.243685)
ON CONFLICT (Warehouse_ID) DO NOTHING;

INSERT INTO Dim_Route (Route_ID, Origin_Warehouse_Key, Destination_Port,
                       Destination_Country, Transport_Mode,
                       Standard_Duration_Days, Base_Cost_USD, Valid_From)
SELECT
    r.route_id, w.Warehouse_Key, r.dest_port, r.dest_country,
    r.mode, r.std_days, r.base_cost, DATE '2024-01-01'
FROM (VALUES
    ('RT-AIR-SIN-LAX', 'WH-02', 'LAX', 'United States', 'AIR',   3, 12500.00),
    ('RT-SEA-RTM-NYC', 'WH-01', 'NYC', 'United States', 'SEA',  21,  3200.00),
    ('RT-RAI-SIN-HCM', 'WH-02', 'SGN', 'Vietnam',       'RAIL',  9,  1800.00)
) AS r(route_id, wh_id, dest_port, dest_country, mode, std_days, base_cost)
JOIN Dim_Warehouse w ON w.Warehouse_ID = r.wh_id;
