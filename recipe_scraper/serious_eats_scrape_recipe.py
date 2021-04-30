import requests
from bs4 import BeautifulSoup
import json
import snowflake.connector
import serious_eats_site_crawler as crawler
import time

def extract_recipe_name(scraped_data):
    recipe_name = scraped_data.find("h1", {"class":"recipe-title"}).get_text()
    return recipe_name

def extract_about_section(scraped_data):
    recipe_about_section = scraped_data.find("ul", {"class":"recipe-about"})
    recipe_about_section_key = recipe_about_section.find_all("span", {"class":"label"})
    recipe_about_section_value = recipe_about_section.find_all("span", {"class":"info"})
    recipe_about_section_dict = {}

    for i in range(0,len(recipe_about_section_key)):
        key = recipe_about_section_key[i].get_text()
        key = key.replace(":","")
        value = recipe_about_section_value[i].get_text()
        recipe_about_section_dict[key]=value

    return recipe_about_section_dict

# Iterate through ingredients list and build an ingredient dictionary
# Returns array of dictionary of ingredients    
def extract_ingredients(scraped_data):
    recipe_section = scraped_data.find("div", {"class":"recipe-ingredients"})
    ingredients_list = recipe_section.find_all("li",{"class":"ingredient"}) # list of ingredients
    recipe_ingredients_list = [] # final list of ingredients that comprise the recipe; list of dictionaries
    ingred_seq = 1
    for i in ingredients_list:
        ingredient_name = i.get_text()
        if i.find("strong") is not None:
            ingredient_type = "Section Header"
        else:
            ingredient_type = "Ingredient"

        if i.find("a") is not None:
            ingredient_linked_recipe = i.a['href']
        else:
            ingredient_linked_recipe = None

        ingredient_dict = {"ingredient": {"ingredient_name": ingredient_name
        , "ingredient_type":ingredient_type
        , "ingredient_linked_recipe":ingredient_linked_recipe
        , "ingredient_sequence": ingred_seq}
        }

        ingred_seq = ingred_seq+1

        recipe_ingredients_list.append((ingredient_dict))
    
    return recipe_ingredients_list

# Returns two dates: published date and last updated date
def extract_dates(scraped_data):
    recipe_publish_section = scraped_data.find("div", {"class":"pubmod-date"})
    recipe_published_date = recipe_publish_section.find("span", {"class":"publish-date"}).get_text()
    if recipe_publish_section.find("span", {"class":"modified-date"}) is not None:
        recipe_last_updated_date = recipe_publish_section.find("span", {"class":"modified-date"}).get_text()
    else: 
        recipe_last_updated_date = "N/A"
    return recipe_published_date, recipe_last_updated_date    

def extract_headnote(scraped_data):
    if scraped_data.find("p", {"class": "headnote"}) is not None:
        recipe_headnote = scraped_data.find("p", {"class": "headnote"}).get_text()
    else:
        recipe_headnote = "N/A"

    return recipe_headnote

def extract_instructions(scraped_data):
    recipe_directions_list = []
    target = scraped_data.find("h2", {"class":"title-section"}, text='Directions')
    for sib in target.find_next_siblings():        
        for item in sib.find_all("li", {"class":"recipe-procedure"}):
            line_number = item.find("div", {"class":"recipe-procedure-number"}).get_text()
            line_direction = item.find("p").get_text()
            recipe_directions_list.append(line_number + ' ' + line_direction)
    
    return recipe_directions_list

def extract_categories(scraped_data):
    recipe_categories_list = []
    breadcrumbs = scraped_data.find("div", {"class":"breadcrumbs__more"})
    for category in breadcrumbs.find_all("strong"):
        recipe_categories_list.append(category.parent['href'])

    return recipe_categories_list

def extract_author_name(scraped_data):
    author_name_span = scraped_data.find("span", {"class": "author-name"})
    author_name = author_name_span.find("a").get_text()
    return author_name

def recipe_to_json(recipe_url):
    print("Beginning to scrape " + url)
    r = requests.get(recipe_url, headers={"User-Agent":"justin.kolpak@gmail.com (Ethical Web Scraper). Email me for details."})
    data = BeautifulSoup(r.text, 'html.parser')

    # TO DO: Add recipe url, recipe comments? 
    recipe_name = extract_recipe_name(data)
    recipe_published_date = extract_dates(data)[0]
    recipe_last_updated_date = extract_dates(data)[1]
    recipe_about_section =  extract_about_section(data)
    recipe_ingredients = extract_ingredients(data)
    recipe_headnote = extract_headnote(data)
    recipe_instructions = extract_instructions(data)
    recipe_categories = extract_categories(data)
    recipe_author_name = extract_author_name(data)

    print("All elements extracted from web page")

    print("Beginning to construct JSON object for " + url)
    #Construct final json
    full_recipe_dict = {
            'system': "Serious Eats"
            , 'recipe_name': recipe_name #value 
            , 'recipe_published_date': recipe_published_date #value 
            , 'recipe_last_updated_date': recipe_last_updated_date #value 
            , 'recipe_about_section': recipe_about_section #dictionary
            , 'recipe_ingredients': recipe_ingredients # array of dictionaries
            , 'recipe_headnote': recipe_headnote #value
            , 'recipe_instructions': recipe_instructions #array
            , 'recipe_categories': recipe_categories #array 
            , 'recipe_author_name': recipe_author_name #value
            }

    full_recipe_json = json.dumps(full_recipe_dict)
    print("JSON object has been created for " + url)    
    return full_recipe_json

def upload_to_snowflake(recipe_name):
    # TO DO: Move to secure location
    print("Establishing connection with Snowflake")
    conn = snowflake.connector.connect( 
            user="a"
            ,password="b!"
            ,account="c"
            ,warehouse="COMPUTE_WH"
            ,database="DBT_POC"
            ,schema="RECIPE")
    print("Snowflake connection established")

    put_result = conn.cursor().execute("PUT file://C:\\Users\\jkolpak\\Desktop\\General\\Learning\\serious-eats-webscraper\\Staging\\" + recipe_name + ".json @JSON_STAGE;")
    print("PUT request to move file to Snowflake stage: " + str(put_result.fetchone()))

    copy_result = conn.cursor().execute("COPY INTO RAW_RECIPE_JSON from @json_stage/" + recipe_name + " file_format='JSON_FILE_FORMAT' ON_ERROR='CONTINUE';")
    print("COPY INTO command to Snowflake table: " + str(copy_result.fetchone()))


## MAIN ##
all_bread_recipe_urls = crawler.get_all_category_urls("https://www.seriouseats.com/recipes/topics/meal/breads")
print("Scraping " + str(len(all_bread_recipe_urls)) + " web pages on www.seriouseats.com")

for url in all_bread_recipe_urls:
    recipe_json = recipe_to_json(url)

    recipe_name = url.rsplit('/', 1)[-1].split(".")[0]
    #recipe_name_clean = recipe_name.replace(" ","_").replace("(","").replace(")","").replace("'","").lower()

    print("Writing file to ../Staging/" + recipe_name + ".json")
    with open('../Staging/' + recipe_name + ".json", 'w') as outfile:
        json.dump(recipe_json, outfile)

    print("File written. Uploading to Snowflake...")

    upload_to_snowflake(recipe_name)
    print("Waiting 5 seconds")
    time.sleep(5)
    print("Wait complete")