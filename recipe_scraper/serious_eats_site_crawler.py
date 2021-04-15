import requests
from bs4 import BeautifulSoup

# Gets the maximum number of pages that have recipes 
def get_max_page_number(cuisine_url):
    section_request = requests.get(cuisine_url, headers={"User-Agent":"justin.kolpak@gmail.com (Ethical Web Scraper). Email me for details."})
    section_data = BeautifulSoup(section_request.text, 'html.parser')
    pagination_menu = section_data.find("div", {"class":"ui-pagination-jump-links"})
    
    if pagination_menu is not None:  
        pagination_menu_filtered = pagination_menu.find_all("a", {"class":"ui-pagination-jump-link"})
    else:
        return 1
    
    page_number_list = []

    for page in pagination_menu_filtered:
        page_number_list.append(int(page.get_text()))


    return max(page_number_list)

# Constructs a list that contains all the valid URLs to crawl	
def build_all_page_urls(cuisine_url):
	max_page_number = get_max_page_number(cuisine_url)
	all_page_urls = []
	for x in range(1,int(max_page_number)+1):
		all_page_urls.append(cuisine_url + "?page=" + str(x) + "#recipes")
        
	return all_page_urls

# For one page, get all recipe URLs
def get_page_recipe_urls(page_url):    
    page_recipe_urls = []
    print("Crawling information for " + page_url)
    section_request = requests.get(page_url, headers={"User-Agent":"justin.kolpak@gmail.com (Ethical Web Scraper). Email me for details."})
    section_data = BeautifulSoup(section_request.text, 'html.parser')
    recipe_section = section_data.find("section", {"class":"c-cards"})
    recipe_modules = recipe_section.find_all("article", {"class":"c-card c-card--small"})
    
    for recipe in recipe_modules:
        page_recipe_urls.append(recipe.find("a", {"class":"c-card__image-container"})['href'])
        
    print("Received recipe information for " + page_url)

    return page_recipe_urls

# Gets all recipe urls for a category (e.g. bread, Mexican, etc.)
def get_all_category_urls(category_url):    
    all_category_urls = []
    all_page_urls = build_all_page_urls(category_url)

    for url in all_page_urls:
        page_url = get_page_recipe_urls(url)
        
        all_category_urls.extend(page_url)

    return all_category_urls

#print(get_all_category_urls("https://www.seriouseats.com/recipes/topics/meal/breads"))


    #r = requests.get(sitemap_url, headers={"User-Agent":"justin.kolpak@gmail.com (Ethical Web Scraper). Email me for details."})
    # data = BeautifulSoup(r.text, 'html.parser')

    # cuisine_categories = ""
    # cuisine_category_urls = [] #summary page for cuisine
    # cuisine_category_page_urls = [] #individual pages that have recipes 
    # total_recipe_urls = [] #all urls 


# target = data.find('h4',text='By Cuisine')
# for sib in target.find_next_siblings():        
#     if sib.name=="h4":        
#         break
#     else:
#         cuisine_categories = sib
        
# for i in cuisine_categories.find_all("li"):
#     cuisine_category_urls.append(i.a['href'])

# for i in cuisine_category_urls:
#     cuisine_category_page_urls.append(build_all_page_urls(i))

#print(get_recipe_urls("https://www.seriouseats.com/recipes/topics/meal/breads?page=16#recipes"))
# for i in cuisine_category_page_urls:
#     for j in i:
#         print(j)

        





    