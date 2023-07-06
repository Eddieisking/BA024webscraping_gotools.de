# BA024webscraping_gotools.de
This project is quite different from the scrapy projects.
The website has used Ajax technology to load its product list pages. So it is impossible to extract the product detailed link from each project pages.
However, from each page of products, we can get the product_id information which is contained in each of Ajax JSON format file. 
Then, it is lucky that the customer reviews link has a very uniform format that facilitates our project, which informs us to just replace the project_id in each link to get the direct Ajax customer reviews.
The detailed process can be summarized as follows.
1. Use search words to open each page of the brand's products.
2. Decode the Ajax link of each product page to find the product_id.
3. Find the Ajax link of each product's customer reviews link and replace the product_id to get all product reviews.
4. Scrapy customer reviews.
