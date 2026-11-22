--
-- PostgreSQL database dump
--

\restrict KzpLGo1fWJoIL44kMf9la39ihZfLDZvKXdONqdzNyCJD2qMTu0mDekrS2AxyB0z

-- Dumped from database version 16.16 (Debian 16.16-1.pgdg13+1)
-- Dumped by pg_dump version 16.16 (Debian 16.16-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS public.fact_shipment DROP CONSTRAINT IF EXISTS fact_shipment_warehouse_key_fkey;
ALTER TABLE IF EXISTS public.fact_shipment DROP CONSTRAINT IF EXISTS fact_shipment_supplier_key_fkey;
ALTER TABLE IF EXISTS public.fact_shipment DROP CONSTRAINT IF EXISTS fact_shipment_route_key_fkey1;
ALTER TABLE IF EXISTS public.fact_shipment DROP CONSTRAINT IF EXISTS fact_shipment_route_key_fkey;
ALTER TABLE IF EXISTS public.fact_shipment DROP CONSTRAINT IF EXISTS fact_shipment_product_key_fkey;
ALTER TABLE IF EXISTS public.fact_shipment DROP CONSTRAINT IF EXISTS fact_shipment_date_key_fkey;
ALTER TABLE IF EXISTS ONLY public.dim_route DROP CONSTRAINT IF EXISTS dim_route_origin_warehouse_key_fkey;
ALTER TABLE IF EXISTS ONLY public.fact_shipment_2024 DROP CONSTRAINT IF EXISTS fact_shipment_2024_pkey;
ALTER TABLE IF EXISTS ONLY public.fact_shipment DROP CONSTRAINT IF EXISTS fact_shipment_pkey;
ALTER TABLE IF EXISTS ONLY public.dim_warehouse DROP CONSTRAINT IF EXISTS dim_warehouse_warehouse_id_key;
ALTER TABLE IF EXISTS ONLY public.dim_warehouse DROP CONSTRAINT IF EXISTS dim_warehouse_pkey;
ALTER TABLE IF EXISTS ONLY public.dim_supplier DROP CONSTRAINT IF EXISTS dim_supplier_pkey;
ALTER TABLE IF EXISTS ONLY public.dim_route DROP CONSTRAINT IF EXISTS dim_route_pkey;
ALTER TABLE IF EXISTS ONLY public.dim_product DROP CONSTRAINT IF EXISTS dim_product_product_id_key;
ALTER TABLE IF EXISTS ONLY public.dim_product DROP CONSTRAINT IF EXISTS dim_product_pkey;
ALTER TABLE IF EXISTS ONLY public.dim_date DROP CONSTRAINT IF EXISTS dim_date_pkey;
ALTER TABLE IF EXISTS ONLY public.dim_date DROP CONSTRAINT IF EXISTS dim_date_full_date_key;
ALTER TABLE IF EXISTS public.dim_warehouse ALTER COLUMN warehouse_key DROP DEFAULT;
ALTER TABLE IF EXISTS public.dim_supplier ALTER COLUMN supplier_key DROP DEFAULT;
ALTER TABLE IF EXISTS public.dim_route ALTER COLUMN route_key DROP DEFAULT;
ALTER TABLE IF EXISTS public.dim_product ALTER COLUMN product_key DROP DEFAULT;
DROP TABLE IF EXISTS public.fact_shipment_2024;
DROP TABLE IF EXISTS public.fact_shipment;
DROP SEQUENCE IF EXISTS public.dim_warehouse_warehouse_key_seq;
DROP TABLE IF EXISTS public.dim_warehouse;
DROP SEQUENCE IF EXISTS public.dim_supplier_supplier_key_seq;
DROP TABLE IF EXISTS public.dim_supplier;
DROP SEQUENCE IF EXISTS public.dim_route_route_key_seq;
DROP TABLE IF EXISTS public.dim_route;
DROP SEQUENCE IF EXISTS public.dim_product_product_key_seq;
DROP TABLE IF EXISTS public.dim_product;
DROP TABLE IF EXISTS public.dim_date;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: dim_date; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dim_date (
    date_key integer NOT NULL,
    full_date date NOT NULL,
    year integer NOT NULL,
    quarter integer NOT NULL,
    month integer NOT NULL,
    month_name text NOT NULL,
    week_of_year integer NOT NULL,
    day_of_week integer NOT NULL,
    is_weekend boolean NOT NULL,
    is_holiday boolean DEFAULT false NOT NULL
);


--
-- Name: dim_product; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dim_product (
    product_key integer NOT NULL,
    product_id text NOT NULL,
    product_name text NOT NULL,
    category text NOT NULL,
    unit_weight_kg numeric(10,3) NOT NULL,
    unit_value_usd numeric(12,2) NOT NULL,
    CONSTRAINT dim_product_unit_value_usd_check CHECK ((unit_value_usd >= (0)::numeric)),
    CONSTRAINT dim_product_unit_weight_kg_check CHECK ((unit_weight_kg > (0)::numeric))
);


--
-- Name: dim_product_product_key_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dim_product_product_key_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dim_product_product_key_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dim_product_product_key_seq OWNED BY public.dim_product.product_key;


--
-- Name: dim_route; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dim_route (
    route_key integer NOT NULL,
    route_id text NOT NULL,
    origin_warehouse_key integer NOT NULL,
    destination_port text NOT NULL,
    destination_country text NOT NULL,
    transport_mode text NOT NULL,
    standard_duration_days integer NOT NULL,
    base_cost_usd numeric(12,2) NOT NULL,
    valid_from date NOT NULL,
    valid_to date DEFAULT '9999-12-31'::date NOT NULL,
    is_current boolean DEFAULT true NOT NULL,
    CONSTRAINT dim_route_base_cost_usd_check CHECK ((base_cost_usd >= (0)::numeric)),
    CONSTRAINT dim_route_standard_duration_days_check CHECK ((standard_duration_days > 0)),
    CONSTRAINT dim_route_transport_mode_check CHECK ((transport_mode = ANY (ARRAY['AIR'::text, 'SEA'::text, 'RAIL'::text, 'ROAD'::text])))
);


--
-- Name: dim_route_route_key_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dim_route_route_key_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dim_route_route_key_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dim_route_route_key_seq OWNED BY public.dim_route.route_key;


--
-- Name: dim_supplier; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dim_supplier (
    supplier_key integer NOT NULL,
    supplier_id text NOT NULL,
    supplier_name text NOT NULL,
    country text NOT NULL,
    reliability_score numeric(3,2) NOT NULL,
    valid_from date NOT NULL,
    valid_to date DEFAULT '9999-12-31'::date NOT NULL,
    is_current boolean DEFAULT true NOT NULL,
    CONSTRAINT dim_supplier_reliability_score_check CHECK (((reliability_score >= (0)::numeric) AND (reliability_score <= (5)::numeric)))
);


--
-- Name: dim_supplier_supplier_key_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dim_supplier_supplier_key_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dim_supplier_supplier_key_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dim_supplier_supplier_key_seq OWNED BY public.dim_supplier.supplier_key;


--
-- Name: dim_warehouse; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.dim_warehouse (
    warehouse_key integer NOT NULL,
    warehouse_id text NOT NULL,
    warehouse_name text NOT NULL,
    city text NOT NULL,
    country text NOT NULL,
    region text NOT NULL,
    latitude numeric(9,6),
    longitude numeric(9,6)
);


--
-- Name: dim_warehouse_warehouse_key_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.dim_warehouse_warehouse_key_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: dim_warehouse_warehouse_key_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.dim_warehouse_warehouse_key_seq OWNED BY public.dim_warehouse.warehouse_key;


--
-- Name: fact_shipment; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fact_shipment (
    shipment_id text NOT NULL,
    date_key integer NOT NULL,
    supplier_key integer NOT NULL,
    warehouse_key integer NOT NULL,
    product_key integer NOT NULL,
    route_key integer NOT NULL,
    quantity_shipped integer NOT NULL,
    shipping_cost_usd numeric(12,2) NOT NULL,
    actual_transit_days integer NOT NULL,
    delay_days integer NOT NULL,
    customs_fee_usd numeric(8,2) DEFAULT 0 NOT NULL,
    damage_flag boolean DEFAULT false NOT NULL,
    avg_standard_duration_days integer NOT NULL,
    shipped_date date NOT NULL,
    CONSTRAINT fact_shipment_actual_transit_days_check CHECK ((actual_transit_days > 0)),
    CONSTRAINT fact_shipment_delay_days_check CHECK ((delay_days >= 0)),
    CONSTRAINT fact_shipment_quantity_shipped_check CHECK ((quantity_shipped > 0)),
    CONSTRAINT fact_shipment_shipping_cost_usd_check CHECK ((shipping_cost_usd >= (0)::numeric))
)
PARTITION BY RANGE (shipped_date);


--
-- Name: fact_shipment_2024; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.fact_shipment_2024 (
    shipment_id text NOT NULL,
    date_key integer NOT NULL,
    supplier_key integer NOT NULL,
    warehouse_key integer NOT NULL,
    product_key integer NOT NULL,
    route_key integer NOT NULL,
    quantity_shipped integer NOT NULL,
    shipping_cost_usd numeric(12,2) NOT NULL,
    actual_transit_days integer NOT NULL,
    delay_days integer NOT NULL,
    customs_fee_usd numeric(8,2) DEFAULT 0 NOT NULL,
    damage_flag boolean DEFAULT false NOT NULL,
    avg_standard_duration_days integer NOT NULL,
    shipped_date date NOT NULL,
    CONSTRAINT fact_shipment_actual_transit_days_check CHECK ((actual_transit_days > 0)),
    CONSTRAINT fact_shipment_delay_days_check CHECK ((delay_days >= 0)),
    CONSTRAINT fact_shipment_quantity_shipped_check CHECK ((quantity_shipped > 0)),
    CONSTRAINT fact_shipment_shipping_cost_usd_check CHECK ((shipping_cost_usd >= (0)::numeric))
);


--
-- Name: fact_shipment_2024; Type: TABLE ATTACH; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fact_shipment ATTACH PARTITION public.fact_shipment_2024 FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');


--
-- Name: dim_product product_key; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dim_product ALTER COLUMN product_key SET DEFAULT nextval('public.dim_product_product_key_seq'::regclass);


--
-- Name: dim_route route_key; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dim_route ALTER COLUMN route_key SET DEFAULT nextval('public.dim_route_route_key_seq'::regclass);


--
-- Name: dim_supplier supplier_key; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dim_supplier ALTER COLUMN supplier_key SET DEFAULT nextval('public.dim_supplier_supplier_key_seq'::regclass);


--
-- Name: dim_warehouse warehouse_key; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dim_warehouse ALTER COLUMN warehouse_key SET DEFAULT nextval('public.dim_warehouse_warehouse_key_seq'::regclass);


--
-- Name: dim_date dim_date_full_date_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dim_date
    ADD CONSTRAINT dim_date_full_date_key UNIQUE (full_date);


--
-- Name: dim_date dim_date_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dim_date
    ADD CONSTRAINT dim_date_pkey PRIMARY KEY (date_key);


--
-- Name: dim_product dim_product_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dim_product
    ADD CONSTRAINT dim_product_pkey PRIMARY KEY (product_key);


--
-- Name: dim_product dim_product_product_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dim_product
    ADD CONSTRAINT dim_product_product_id_key UNIQUE (product_id);


--
-- Name: dim_route dim_route_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dim_route
    ADD CONSTRAINT dim_route_pkey PRIMARY KEY (route_key);


--
-- Name: dim_supplier dim_supplier_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dim_supplier
    ADD CONSTRAINT dim_supplier_pkey PRIMARY KEY (supplier_key);


--
-- Name: dim_warehouse dim_warehouse_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dim_warehouse
    ADD CONSTRAINT dim_warehouse_pkey PRIMARY KEY (warehouse_key);


--
-- Name: dim_warehouse dim_warehouse_warehouse_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dim_warehouse
    ADD CONSTRAINT dim_warehouse_warehouse_id_key UNIQUE (warehouse_id);


--
-- Name: fact_shipment fact_shipment_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fact_shipment
    ADD CONSTRAINT fact_shipment_pkey PRIMARY KEY (shipped_date, shipment_id);


--
-- Name: fact_shipment_2024 fact_shipment_2024_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.fact_shipment_2024
    ADD CONSTRAINT fact_shipment_2024_pkey PRIMARY KEY (shipped_date, shipment_id);


--
-- Name: fact_shipment_2024_pkey; Type: INDEX ATTACH; Schema: public; Owner: -
--

ALTER INDEX public.fact_shipment_pkey ATTACH PARTITION public.fact_shipment_2024_pkey;


--
-- Name: dim_route dim_route_origin_warehouse_key_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.dim_route
    ADD CONSTRAINT dim_route_origin_warehouse_key_fkey FOREIGN KEY (origin_warehouse_key) REFERENCES public.dim_warehouse(warehouse_key);


--
-- Name: fact_shipment fact_shipment_date_key_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.fact_shipment
    ADD CONSTRAINT fact_shipment_date_key_fkey FOREIGN KEY (date_key) REFERENCES public.dim_date(date_key);


--
-- Name: fact_shipment fact_shipment_product_key_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.fact_shipment
    ADD CONSTRAINT fact_shipment_product_key_fkey FOREIGN KEY (product_key) REFERENCES public.dim_product(product_key);


--
-- Name: fact_shipment fact_shipment_route_key_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.fact_shipment
    ADD CONSTRAINT fact_shipment_route_key_fkey FOREIGN KEY (route_key) REFERENCES public.dim_route(route_key);


--
-- Name: fact_shipment fact_shipment_route_key_fkey1; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.fact_shipment
    ADD CONSTRAINT fact_shipment_route_key_fkey1 FOREIGN KEY (route_key) REFERENCES public.dim_route(route_key);


--
-- Name: fact_shipment fact_shipment_supplier_key_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.fact_shipment
    ADD CONSTRAINT fact_shipment_supplier_key_fkey FOREIGN KEY (supplier_key) REFERENCES public.dim_supplier(supplier_key);


--
-- Name: fact_shipment fact_shipment_warehouse_key_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE public.fact_shipment
    ADD CONSTRAINT fact_shipment_warehouse_key_fkey FOREIGN KEY (warehouse_key) REFERENCES public.dim_warehouse(warehouse_key);


--
-- PostgreSQL database dump complete
--

\unrestrict KzpLGo1fWJoIL44kMf9la39ihZfLDZvKXdONqdzNyCJD2qMTu0mDekrS2AxyB0z

