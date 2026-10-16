USE RetailDW;
GO

CREATE VIEW vw_monthly_sales_by_region AS
SELECT d.order_year, d.order_month, d.month_name, l.region,       
       SUM(f.sales) AS total_sales, SUM(f.profit) AS total_profit
FROM fact_sales f
JOIN dim_date d ON f.order_date_key = d.date_key
JOIN dim_location l ON f.location_key = l.location_key
GROUP BY d.order_year, d.order_month, d.month_name, l.region;
GO

CREATE VIEW vw_product_profit_rank AS
SELECT p.category, p.sub_category, p.product_name,       
       SUM(f.profit) AS total_profit,       
       RANK() OVER (PARTITION BY p.category ORDER BY SUM(f.profit) DESC) AS rank_in_category
FROM fact_sales f
JOIN dim_product p ON f.product_id = p.product_id
GROUP BY p.category, p.sub_category, p.product_name;
GO

CREATE PROCEDURE usp_sales_by_year @year INT AS
BEGIN
    SELECT l.region, p.category,           
           SUM(f.sales) AS total_sales, SUM(f.profit) AS total_profit
    FROM fact_sales f
    JOIN dim_date d ON f.order_date_key = d.date_key
    JOIN dim_location l ON f.location_key = l.location_key
    JOIN dim_product p ON f.product_id = p.product_id
    WHERE d.order_year = @year
    GROUP BY l.region, p.category
    ORDER BY total_sales DESC;
END;
GO

EXEC usp_sales_by_year 2017;