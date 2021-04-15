import snowflake.connector as snf
import snowflake.connector.pandas_tools as snf_pandas
import pandas as pd
import recipe_crf_model_predict as predict
import recipe_crf_model_data_prep as prep

''' TO DO LIST:
- 1/3 and 2/3 fractions (likely any that have repeating decimals) are not populating QUANTITY
- "1/4 cup/ 35g yellow corn" - cup and / are being identified as one word, can't separate based on / 
- 5g not registering as 5 grams
- Handle multiple quantities / units in one ingredient
'''


conn = snf.connect( 
            user="b"
            ,password="x"
            ,account="c"
            ,warehouse="COMPUTE_WH"
            ,database="DBT_POC"
            ,schema="RECIPE")
# Create a cursor object.
cur = conn.cursor()

# Execute a statement that will generate a result set.
sql = "SELECT * FROM RECIPE_INGREDIENT"
cur.execute(sql)

# Fetch the result set from the cursor and deliver it as the Pandas DataFrame.
df = cur.fetch_pandas_all()

df['INGREDIENT_NAME_CRF_FMT'] = df['INGREDIENT_NAME'].map(lambda x: prep.sentence_format_for_crf(x)[0])

df['PREDICTION_RESULTS_RAW'] = \
    df['INGREDIENT_NAME'] \
        .map(lambda x: predict.sentence_predict_label(x, 'recipetagging-v5.crfsuite'))

df['PREDICTION_RESULTS_FMT'] = \
    df.apply(lambda x: predict.format_prediction(x.INGREDIENT_NAME, x.PREDICTION_RESULTS_RAW), axis=1)

df['NAME'] = df['PREDICTION_RESULTS_FMT'].map(lambda x: predict.get_name_from_prediction(x))
df['QUANTITY'] = df['PREDICTION_RESULTS_FMT'].map(lambda x: predict.get_qty_from_prediction(x))
df['UNIT'] = df['PREDICTION_RESULTS_FMT'].map(lambda x: predict.get_unit_from_prediction(x))
df['ETL_LAST_UPDATED'] = df.ETL_LAST_UPDATED.dt.date # Snowflake library has problem with writing timestamps, using date

final_df = df[['RECIPE_INGREDIENT_ID','RECIPE_NAME','INGREDIENT_NAME','RECIPE_SECTION','ETL_LAST_UPDATED','NAME','QUANTITY','UNIT']]

#print(final_df[final_df['RECIPE_NAME'] == 'Cheddar Scones with Chive Butter Recipe'])
truncate_sql = "TRUNCATE TABLE RECIPE_INGREDIENT_LABELED"
cur.execute(truncate_sql)

snf_pandas.write_pandas(conn = conn, df = final_df, table_name = "RECIPE_INGREDIENT_LABELED")
