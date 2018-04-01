#!/usr/bin/env python
# Cocktail Scraping script for thecocktaildb.com
# This program utilizes the api found at https://www.thecocktaildb.com/api.php
# to scrape all drinks and put them into excel spreadsheets. This will be
# utilized later on to import the data into MySQL
#


# Imports
import requests
import json
import pymysql.cursors
# import os

from secrets import mysql_password

connection = pymysql.connect(host='localhost',
							 user='root',
							 password=mysql_password,
							 db='cocktail_search',
							 charset='utf8mb4',
							 autocommit=True)

cursor = connection.cursor()

# IMPORTING DRINKS
# First get all alcoholic and nonalcoholic drinks.
alcoholic = requests.get(
	"https://www.thecocktaildb.com/api/json/v1/1/filter.php?a=Alcoholic")
nonalcoholic = requests.get(
	"https://www.thecocktaildb.com/api/json/v1/1/filter.php?a=Non_Alcoholic")

# Convert to JSON format for easy iteration
alcoholic = alcoholic.json()["drinks"]
nonalcoholic = nonalcoholic.json()["drinks"]


length = len(alcoholic)
i = 0
for drink in alcoholic:
	i = i + 1
	print("[%d of %d]: %s" % (i, length, drink["strDrink"]))
	# Get each drink's info
	drinkrequest = requests.get(
		"https://www.thecocktaildb.com/api/json/v1/1/lookup.php?i=%d" % ((int)(drink["idDrink"])))

	# Convert to JSON format
	drinkrequest = drinkrequest.json()["drinks"][0]

	# Get the category ID
	categoryQuery = "select category_id from categories where name like \"%s\";" % drinkrequest[
		"strCategory"]

	cursor.execute(categoryQuery)

	categoryID = int(cursor.fetchone()[0])

	# Get the glass ID
	glassQuery = "select glass_id from glasses where name like \"%s\";" % drinkrequest[
		"strGlass"]

	cursor.execute(glassQuery)

	glassID = int(cursor.fetchone()[0])


	# Get if it is alcoholic
	alcoholic = 1 if (drinkrequest["strAlcoholic"] == "Alcoholic") else 0


	# Insert the recipe
	recipe_ingredient_insert = "insert into recipes(name,category_id,glass_id,instructions,picture,isAlcoholic) values (\"%s\",%s,%s,\"%s\",\"%s\",%s);"
	cursor.execute(recipe_ingredient_insert,(drinkrequest["strDrink"],categoryID,glassID,drinkrequest["strInstructions"],drinkrequest["strDrinkThumb"],alcoholic));

	cursor.execute("SELECT LAST_INSERT_ID();");

	recipeID = int(cursor.fetchone()[0]) 


	ingredient_num = 1;
	# Insert ingredients
	while(ingredient_num < 16 and drinkrequest["strIngredient%d" % ingredient_num] != ""):
		try:
			# Get or add the UOM
			# print("|%s|" % drinkrequest["strMeasure%d" % ingredient_num])
			if drinkrequest["strMeasure%d" % ingredient_num] != "\\n":
				# print("INNER!")
				bigunit = drinkrequest["strMeasure%d" % ingredient_num]

				unit = bigunit.split(" ")[-2]
				amount = bigunit.replace(" " + unit+ " ", "");

				uomQuery = "select exists(select * from units_of_measure where amount = \"%s\" AND unit = \"%s\");" % (amount, unit)

				cursor.execute(uomQuery)

				result = int(cursor.fetchone()[0])

				if result == 0:
					uomQueryInsert = "insert into units_of_measure(amount,unit) values (\"%s\",\"%s\")" % (amount,unit)
					cursor.execute(uomQueryInsert);
				

				uomIDQuery = "select uom_id from units_of_measure where amount = \"%s\" and unit = \"%s\"" % (amount,unit);

				cursor.execute(uomIDQuery);

				uomID = int(cursor.fetchone()[0])

				ingredientExistsQuery = "select exists(select * from ingredients where name like \"%s\");" % drinkrequest["strIngredient%d" % ingredient_num]

				cursor.execute(ingredientExistsQuery);

				result = int(cursor.fetchone()[0]);
				if result == 1:
					ingredientIDQuery = "select ingredient_id from ingredients where name like \"%s\"" % drinkrequest["strIngredient%d" % ingredient_num]
					cursor.execute(ingredientIDQuery);

				else:
					cursor.execute("insert into ingredients(name) values (\"%s\");" % (drinkrequest["strIngredient%d" % ingredient_num]))
					cursor.execute("SELECT LAST_INSERT_ID();")

				ingredientID = int(cursor.fetchone()[0]);

				insertRecipeIngredientQuery = "insert into recipe_ingredients(recipe_id,ingredient_id,uom_id) values (%s,%s,%s);" % (recipeID,ingredientID,uomID);

				cursor.execute(insertRecipeIngredientQuery);
				# print("FINISHING!!!")

		except Exception as e:
			print(e);

		ingredient_num = ingredient_num + 1;





	

## IMPORTING INGREDIENTS ##
# ingredients = requests.get("https://www.thecocktaildb.com/api/json/v1/1/list.php?i=list")

# ingredients = ingredients.json()["drinks"]

# length = len(ingredients)
# iter = 0;
# for ingredient in ingredients:
# 	iter = iter + 1;
# 	print("[%3d of %d]: %s" % (iter,length,ingredient["strIngredient1"]))
# 	query = "insert into ingredients(name) values (\"%s\");" % ingredient["strIngredient1"]
# 	cursor.execute(query);


# ## IMPORTING GLASSES ##
# glasses = requests.get("https://www.thecocktaildb.com/api/json/v1/1/list.php?g=list")

# glasses = glasses.json()["drinks"]

# length = len(glasses)
# iter = 0;
# for glass in glasses:
# 	iter = iter + 1;
# 	print("[%3d of %d]: %s" % (iter,length,glass["strGlass"]))
# 	query = "insert into glasses(name) values (\"%s\");" % glass["strGlass"]
# 	cursor.execute(query);
