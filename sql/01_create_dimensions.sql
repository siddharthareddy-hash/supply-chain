CREATE TABLE IF NOT EXISTS Dim_Date (
    Date_Key         INT PRIMARY KEY,          -- yyyymmdd
    Full_Date        DATE NOT NULL UNIQUE,
    Year             INT  NOT NULL,
    Quarter          INT  NOT NULL,
    Month            INT  NOT NULL,
    Month_Name       TEXT NOT NULL,
    Week_Of_Year     INT  NOT NULL,
    Day_Of_Week      INT  NOT NULL,
    Is_Weekend       BOOLEAN NOT NULL,
    Is_Holiday       BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS Dim_Supplier (
    Supplier_Key      SERIAL PRIMARY KEY,
    Supplier_ID       TEXT NOT NULL,
    Supplier_Name     TEXT NOT NULL,
    Country           TEXT NOT NULL,
    Reliability_Score NUMERIC(3,2) NOT NULL
                      CHECK (Reliability_Score BETWEEN 0 AND 5),
    -- SCD Type 2
    Valid_From        DATE NOT NULL,
    Valid_To          DATE NOT NULL DEFAULT DATE '9999-12-31',
    Is_Current        BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS Dim_Warehouse (
    Warehouse_Key   SERIAL PRIMARY KEY,
    Warehouse_ID    TEXT NOT NULL UNIQUE,
    Warehouse_Name  TEXT NOT NULL,
    City            TEXT NOT NULL,
    Country         TEXT NOT NULL,
    Region          TEXT NOT NULL,
    Latitude        NUMERIC(9,6),
    Longitude       NUMERIC(9,6)
);

CREATE TABLE IF NOT EXISTS Dim_Product (
    Product_Key    SERIAL PRIMARY KEY,
    Product_ID     TEXT NOT NULL UNIQUE,
    Product_Name   TEXT NOT NULL,
    Category       TEXT NOT NULL,
    Unit_Weight_Kg NUMERIC(10,3) NOT NULL CHECK (Unit_Weight_Kg > 0),
    Unit_Value_USD NUMERIC(12,2) NOT NULL CHECK (Unit_Value_USD >= 0)
);

CREATE TABLE IF NOT EXISTS Dim_Route (
    Route_Key               SERIAL PRIMARY KEY,
    Route_ID                TEXT NOT NULL,
    Origin_Warehouse_Key    INT NOT NULL REFERENCES Dim_Warehouse(Warehouse_Key),
    Destination_Port        TEXT NOT NULL,
    Destination_Country     TEXT NOT NULL,
    Transport_Mode          TEXT NOT NULL
                            CHECK (Transport_Mode IN ('AIR','SEA','RAIL','ROAD')),
    Standard_Duration_Days  INT NOT NULL CHECK (Standard_Duration_Days > 0),
    Base_Cost_USD           NUMERIC(12,2) NOT NULL CHECK (Base_Cost_USD >= 0),
    -- SCD Type 2
    Valid_From              DATE NOT NULL,
    Valid_To                DATE NOT NULL DEFAULT DATE '9999-12-31',
    Is_Current              BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE TABLE IF NOT EXISTS Fact_ML_Predictions (
    Prediction_ID   BIGSERIAL PRIMARY KEY,
    Model_Name      TEXT NOT NULL,
    Model_Version   TEXT NOT NULL,
    Route_Key       INT REFERENCES Dim_Route(Route_Key),
    Shipment_ID     TEXT,
    Prediction_Date INT NOT NULL REFERENCES Dim_Date(Date_Key),
    Target_Date     INT NOT NULL REFERENCES Dim_Date(Date_Key),
    Yhat            NUMERIC(12,4),
    Yhat_Lower      NUMERIC(12,4),
    Yhat_Upper      NUMERIC(12,4),
    Anomaly_Score   NUMERIC(8,6),
    Is_Anomaly      BOOLEAN,
    Created_At      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS DQ_Quarantine (
    Quarantine_ID  BIGSERIAL PRIMARY KEY,
    Source_Table   TEXT NOT NULL,
    Rejected_Row   JSONB NOT NULL,
    Failure_Reason TEXT NOT NULL,
    Failed_At      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
