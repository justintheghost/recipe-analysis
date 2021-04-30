{{ config(materialized='view') }}

with to_grams AS (
SELECT COALESCE(i_w.CONVERSION_FACTOR,i_v.CONVERSION_FACTOR) AS CONVERSION_FACTOR_TO_GRAM
  , COALESCE(TRY_TO_DECIMAL(r.QUANTITY),1) * COALESCE(i_w.CONVERSION_FACTOR,i_v.CONVERSION_FACTOR) AS QUANTITY_GRAM  
  , CASE WHEN NAME LIKE '%flour%' THEN 1 ELSE 0 END AS FLOUR_FLAG       
  , r.*
  , i_w.*  
  , c.*
  , i.INGREDIENT_CATEGORY 
  , i.INGREDIENT_NAME AS INGREDIENT_NAME_ING 
  , i.INGREDIENT_ID
  , imm.MASTERED_INGREDIENT_NAME
FROM RECIPE_INGREDIENT_LABELED r
LEFT JOIN INGREDIENT_MASTER_MAPPING imm ON r.NAME = imm.RAW_INGREDIENT_NAME
LEFT JOIN UOM_MAP_CATEGORY c ON r.UNIT = c.UNIT_OF_MEASUREMENT
LEFT JOIN UOM_MAP_ITEM i_w on r.UNIT = i_w.SOURCE_UNIT AND c.CATEGORY = 'weight'
LEFT JOIN UOM_MAP_ITEM i_v ON imm.MASTERED_INGREDIENT_NAME = i_v.SOURCE_INGREDIENT AND r.UNIT = i_v.SOURCE_UNIT AND c.CATEGORY = 'volume'
LEFT JOIN INGREDIENT i ON imm.MASTERED_INGREDIENT_NAME = i.INGREDIENT_NAME
), add_ff AS (
SELECT 
CASE WHEN FLOUR_FLAG = 1 THEN QUANTITY_GRAM ELSE NULL END AS QUANTITY_GRAM_FLOUR
    , NAME AS RAW_INGREDIENT_NAME
    , QUANTITY AS INGREDIENT_QUANTITY
    , UNIT AS INGREDIENT_UNIT    
    , *
FROM to_grams t
ORDER BY RECIPE_NAME
), final as (
SELECT * 
    , SUM(QUANTITY_GRAM_FLOUR) OVER (PARTITION BY RECIPE_NAME) AS FLOUR_AMOUNT
    , QUANTITY_GRAM / SUM(QUANTITY_GRAM_FLOUR) OVER (PARTITION BY RECIPE_NAME) * 100 AS BAKERS_PERCENTAGE    
FROM add_ff
  )
  
    , dq AS (
select CASE WHEN BAKERS_PERCENTAGE IS NULL THEN 1 ELSE 0 END IS_NOT_POPULATED, * from final
)
SELECT    
ETL_LAST_UPDATED
    , RAW_INGREDIENT_NAME
    , MASTERED_INGREDIENT_NAME
    , INGREDIENT_QUANTITY
    , INGREDIENT_UNIT
    , RECIPE_NAME    
    , BAKERS_PERCENTAGE
    , FLOUR_AMOUNT    
    , INGREDIENT_CATEGORY
FROM DQ
WHERE RECIPE_NAME IN (
  SELECT RECIPE_NAME FROM dq
  GROUP BY RECIPE_NAME
  HAVING SUM(IS_NOT_POPULATED) = 0
  )