CREATE TABLE IF NOT EXISTS Fact_Shipment (
    Shipment_ID                  TEXT NOT NULL,
    Date_Key                     INT  NOT NULL REFERENCES Dim_Date(Date_Key),
    Supplier_Key                 INT  NOT NULL REFERENCES Dim_Supplier(Supplier_Key),
    Warehouse_Key                INT  NOT NULL REFERENCES Dim_Warehouse(Warehouse_Key),
    Product_Key                  INT  NOT NULL REFERENCES Dim_Product(Product_Key),
    Route_Key                    INT  NOT NULL REFERENCES Dim_Route(Route_Key),
    Quantity_Shipped             INT  NOT NULL CHECK (Quantity_Shipped > 0),
    Shipping_Cost_USD            NUMERIC(12,2) NOT NULL CHECK (Shipping_Cost_USD >= 0),
    Actual_Transit_Days          INT  NOT NULL CHECK (Actual_Transit_Days > 0),
    Delay_Days                   INT  NOT NULL CHECK (Delay_Days >= 0),  -- computed in ETL
    Customs NUMERIC(8,2) NOT NULL DEFAULT 0,
    Damage_Flag                  BOOLEAN NOT NULL DEFAULT FALSE,
    Avg_Standard_Duration_Days   INT  NOT NULL,  -- denormalized from route version
    Shipped_Date                 DATE NOT NULL,
    PRIMARY KEY (Shipped_Date, Shipment_ID),
    FOREIGN KEY (Route_Key) REFERENCES Dim_Route(Route_Key)
) PARTITION BY RANGE (Shipped_Date);

-- Create 12 monthly partitions for the first year (extend as needed)
DO DECLAREmDATE:=DATE′2024−01−01′;iIN0..11LOOPEXECUTEformat(′CREATETABLEIFNOTEXISTSFactShipmentFORVALUESFROM(tochar(m,′YYYYMM′),m,m+INTERVAL′1month′);m:=m+INTERVAL′1month′;ENDLOOP;ENDDECLARE
    m DATE := DATE '2024-01-01';
 i IN 0..11 LOOP
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS Fact_Shipment_%s PARTITION OF Fact_Shipment
             FOR VALUES FROM (%L) TO (%L)',
            to_char(m, 'YYYY_MM'), m, m + INTERVAL '1 month');
        m := m + INTERVAL '1 month';
    END LOOP;
ENDDECLAREmDATE:=DATE′2024−01−01′;iIN0..11LOOPEXECUTEformat(′CREATETABLEIFNOTEXISTSFactS​hipmentF​ORVALUESFROM(toc​har(m,′YYYYM​M′),m,m+INTERVAL′1month′);m:=m+INTERVAL′1month′;ENDLOOP;END;

CREATE INDEX IF NOT EXISTS idx_shipment_date   ON Fact_Shipment (Date_Key);
CREATE INDEX IF NOT EXISTS idx_shipment_route  ON Fact_Shipment (Route_Key);
CREATE INDEX IF NOT EXISTS idx_shipment_supp   ON Fact_Shipment (Supplier_Key);
CREATE INDEX IF NOT EXISTS idx_shipment_date_route ON Fact_Shipment (Date_Key, Route_Key);

CREATE TABLE IF NOT EXISTS Fact_ML_Predictions (
    Prediction_ID   BIGSERIAL PRIMARY KEY,
    Model_Name      TEXT NOT NULL,           -- 'prophet_route_delay' | 'iso_forest'
    Model_Version   TEXT NOT NULL,
    Route_Key       INT REFERENCES Dim_Route(Route_Key),
    Shipment_ID     TEXT,                    -- for anomaly flags
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
