import time
import json
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Initialize WebDriver
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 10)
actions = ActionChains(driver)
data = {}
links_data = []  # This will store the links to be written to CSV

driver.get("https://iwandw.com")
time.sleep(2)

try:
    # Click on "Products"
    products_menu = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Products")))
    products_menu.click()
    time.sleep(2)

    categories = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.menu-item-has-children > a")))

    for category in categories:
        category_name = category.text.strip()
        print(f"\n➡️ Clicking on Category: {category_name}")

        actions.move_to_element(category).perform()
        time.sleep(2)
        category.click()
        time.sleep(2)

        subcategories = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//ul[@class='sub-menu']/li/a")))
        data[category_name] = {}

        for subcategory in subcategories:
            subcategory_name = subcategory.text.strip()
            subcategory_url = subcategory.get_attribute("href")
            print(f"   ➡️ Clicking on Subcategory: {subcategory_name}")

            driver.execute_script("window.open(arguments[0], '_blank');", subcategory_url)
            driver.switch_to.window(driver.window_handles[1])
            time.sleep(2)

            # Scroll to load all products
            for _ in range(4):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            product_names = []

            if subcategory_name.lower() in ["bathroom", "bathroom accessories"]:
                product_elements = soup.find_all('div', class_='card-subcategoria__titulo')
            else:
                product_elements = soup.find_all('div', class_='card-producto__titulo')

            if product_elements:
                for product_element in product_elements:
                    product_name = product_element.text.strip()
                    print(f"   ➡️ Clicking on Product: {product_name}")

                    product_link = product_element.find_parent('a')
                    if product_link:
                        product_url = product_link.get('href')
                        driver.execute_script("window.open(arguments[0], '_blank');", product_url)
                        driver.switch_to.window(driver.window_handles[2])
                        time.sleep(2)

                        data[category_name].setdefault(subcategory_name, {})[product_name] = {}
                        soup = BeautifulSoup(driver.page_source, "html.parser")

                        # Extract Technical Info for product
                        try:
                            tech_guide = wait.until(EC.presence_of_element_located(
                                (By.CSS_SELECTOR, ".vtm-item-acordeon-icono-derecha__titulo")
                            ))
                            tech_guide_link = tech_guide.get_attribute("href")

                            if tech_guide_link:
                                print(f"      📥 Downloading Technical Guide for Product: {tech_guide_link}")
                                data[category_name][subcategory_name][product_name]["technical_guide"] = tech_guide_link
                                # Save link to CSV
                                links_data.append({
                                    'Category': category_name,
                                    'Subcategory': subcategory_name,
                                    'Product': product_name,
                                    'Guide Type': 'Technical Guide',
                                    'Link': tech_guide_link
                                })
                                
                        except Exception:
                            print(f"      ❌ No Technical Guide Found for Product: {product_name}")

                        # Extract Installation Guide for product
                        try:
                            soup = BeautifulSoup(driver.page_source, "html.parser")
                            install_guide_divs = soup.find_all('div', href=True, class_='vtm-item-acordeon-icono-derecha__titulo')
                            valid_links = [div['href'] for div in install_guide_divs if any(keyword in div['href'].lower() for keyword in ['guide', 'installation', 'manual'])]

                            if valid_links:
                                for install_guide_link in valid_links:
                                    print(f"      📥 Downloading Installation Guide for Product: {install_guide_link}")
                                    data[category_name][subcategory_name][product_name]["installation_guide"] = install_guide_link
                                    # Save link to CSV
                                    links_data.append({
                                        'Category': category_name,
                                        'Subcategory': subcategory_name,
                                        'Product': product_name,
                                        'Guide Type': 'Installation Guide',
                                        'Link': install_guide_link
                                    })
                                    
                        except Exception:
                            print(f"      ❌ No Installation Guide Found for Product: {product_name}")

                        # Extract Maintenance & Warranty Guide for product
                        try:
                            warranty_guides = soup.find_all("div", class_="vtm-item-acordeon-icono-derecha__titulo", href=True)
                            for guide in warranty_guides:
                                warranty_link = guide.get("href")
                                if "maintenance" in warranty_link.lower():  # Check if it's a warranty guide
                                    print(f"      📥 Downloading Maintenance & Warranty Guide: {warranty_link}")
                                    data[category_name][subcategory_name][product_name]["maintenance_warranty"] = warranty_link
                                    # Save link to CSV
                                    links_data.append({
                                        'Category': category_name,
                                        'Subcategory': subcategory_name,
                                        'Product': product_name,
                                        'Guide Type': 'Maintenance & Warranty Guide',
                                        'Link': warranty_link
                                    })
                        except Exception:
                            print(f"      ❌ No Maintenance & Warranty Guide Found for {product_name}")

                        # Extract 3D finishes for product
                        try:
                            finishes = soup.find_all("div", class_="vtm-item-grid-acabado")  # Update with the correct class
                            product_finish_list = []
                            for finish in finishes:
                                finish_name_elem = finish.find("div", class_="vtm-item-grid-acabado__nombre")
                                finish_ref_elem = finish.find("div", class_="vtm-item-grid-acabado__referencia")
                                if finish_name_elem and finish_ref_elem:
                                    finish_name = finish_name_elem.text.strip()
                                    finish_ref = finish_ref_elem.text.strip()
                                    product_finish_list.append({"name": finish_name, "reference": finish_ref})
                            if product_finish_list:
                                print(f"      📌 Extracted 3D finishes for Product: {product_finish_list}")
                                data[category_name][subcategory_name][product_name]["3d_finishes"] = product_finish_list
                                # Save 3D finishes to CSV
                                for finish in product_finish_list:
                                    links_data.append({
                                        'Category': category_name,
                                        'Subcategory': subcategory_name,
                                        'Product': product_name,
                                        '3D Finish': finish["name"],
                                        'Reference': finish["reference"]
                                    })
                        except Exception:
                            print(f"      ❌ No 3D finishes found for Product: {product_name}")

                        # Click on each sub-product
                        sub_products = []
                        sub_product_elements = driver.find_elements(By.CLASS_NAME, "card-producto__titulo")

                        for sub_product_element in sub_product_elements:
                            sub_product_name = sub_product_element.text.strip()
                            sub_products.append(sub_product_name)
                            print(f"      ➡️ Found Sub-product: {sub_product_name}")

                        if sub_products:
                            data[category_name][subcategory_name][product_name]["sub_products"] = sub_products
                            print(f"   ✅ Sub-products for {product_name}: {sub_products}")

                        for i in range(len(sub_products)):
                            sub_product_elements = driver.find_elements(By.CLASS_NAME, "card-producto__titulo")
                            if i >= len(sub_product_elements):
                                break  # Avoid stale elements

                            sub_product_element = sub_product_elements[i]
                            sub_product_name = sub_product_element.text.strip()

                            try:
                                print(f"      🖱️ Clicking on Sub-product: {sub_product_name}")
                                driver.execute_script("arguments[0].click();", sub_product_element)
                                time.sleep(2)

                                # Extract Sub-product information
                                soup = BeautifulSoup(driver.page_source, "html.parser")
                                description = soup.find("div", class_="zona-superior__descripcion-corta")
                                description_text = description.text.strip() if description else "No description found"
                                print(f"      📌 Extracted Description: {description_text}")

                                data[category_name][subcategory_name][product_name].setdefault("sub_product_details", {})[sub_product_name] = {
                                    "description": description_text
                                }

                                # Download the Technical Guide for Sub-product
                                try:
                                    tech_guide = wait.until(EC.presence_of_element_located(
                                        (By.CSS_SELECTOR, ".vtm-item-acordeon-icono-derecha__titulo")
                                    ))
                                    tech_guide_link = tech_guide.get_attribute("href")

                                    if tech_guide_link:
                                        print(f"      📥 Downloading Technical Guide for Sub-product: {tech_guide_link}")
                                        data[category_name][subcategory_name][product_name]["sub_product_details"][sub_product_name]["technical_guide"] = tech_guide_link
                                        # Save link to CSV
                                        links_data.append({
                                            'Category': category_name,
                                            'Subcategory': subcategory_name,
                                            'Product': product_name,
                                            'Sub-product': sub_product_name,
                                            'Guide Type': 'Technical Guide',
                                            'Link': tech_guide_link
                                        })
                                        
                                except Exception:
                                    print(f"      ❌ No Technical Guide Found for Sub-product: {sub_product_name}")

                                # Extract Installation Guide for Sub-product
                                try:
                                    soup = BeautifulSoup(driver.page_source, "html.parser")
                                    install_guide_divs = soup.find_all('div', href=True, class_='vtm-item-acordeon-icono-derecha__titulo')

                                    valid_links = [div['href'] for div in install_guide_divs if any(keyword in div['href'].lower() for keyword in ['guide', 'installation', 'manual'])]
                                    if valid_links:
                                        for install_guide_link in valid_links:
                                            print(f"      📥 Downloading Installation Guide for Sub-product: {install_guide_link}")
                                            data[category_name][subcategory_name][product_name]["sub_product_details"][sub_product_name]["installation_guide"] = install_guide_link
                                            # Save link to CSV
                                            links_data.append({
                                                'Category': category_name,
                                                'Subcategory': subcategory_name,
                                                'Product': product_name,
                                                'Sub-product': sub_product_name,
                                                'Guide Type': 'Installation Guide',
                                                'Link': install_guide_link
                                            })
                                            
                                except Exception:
                                    print(f"      ❌ No Installation Guide Found for Sub-product: {sub_product_name}")

                                # Extract Maintenance & Warranty Guide for Sub-product
                                try:
                                    warranty_guides = soup.find_all("div", class_="vtm-item-acordeon-icono-derecha__titulo", href=True)
                                    for guide in warranty_guides:
                                        warranty_link = guide.get("href")
                                        if "maintenance" in warranty_link.lower():  # Check if it's a warranty guide
                                            print(f"      📥 Downloading Maintenance & Warranty Guide for Sub-product: {warranty_link}")
                                            data[category_name][subcategory_name][product_name]["sub_product_details"][sub_product_name]["maintenance_warranty"] = warranty_link
                                            # Save link to CSV
                                            links_data.append({
                                                'Category': category_name,
                                                'Subcategory': subcategory_name,
                                                'Product': product_name,
                                                'Sub-product': sub_product_name,
                                                'Guide Type': 'Maintenance & Warranty Guide',
                                                'Link': warranty_link
                                            })
                                            
                                except Exception:
                                    print(f"      ❌ No Maintenance & Warranty Guide Found for {sub_product_name}")

                                # Extract 3D finishes for Sub-product
                                try:
                                    finishes = soup.find_all("div", class_="vtm-item-grid-acabado")  # Update with the correct class
                                    sub_product_finish_list = []
                                    for finish in finishes:
                                        finish_name_elem = finish.find("div", class_="vtm-item-grid-acabado__nombre")
                                        finish_ref_elem = finish.find("div", class_="vtm-item-grid-acabado__referencia")
                                        if finish_name_elem and finish_ref_elem:
                                            finish_name = finish_name_elem.text.strip()
                                            finish_ref = finish_ref_elem.text.strip()
                                            sub_product_finish_list.append({"name": finish_name, "reference": finish_ref})
                                    if sub_product_finish_list:
                                        print(f"      📌 Extracted 3D finishes for Sub-product: {sub_product_finish_list}")
                                        data[category_name][subcategory_name][product_name]["sub_product_details"][sub_product_name]["3d_finishes"] = sub_product_finish_list
                                        # Save 3D finishes to CSV
                                        for finish in sub_product_finish_list:
                                            links_data.append({
                                                'Category': category_name,
                                                'Subcategory': subcategory_name,
                                                'Product': product_name,
                                                'Sub-product': sub_product_name,
                                                '3D Finish': finish["name"],
                                                'Reference': finish["reference"]
                                            })
                                except Exception:
                                    print(f"      ❌ No 3D finishes found for Sub-product: {sub_product_name}")

                                driver.back()
                                time.sleep(2)

                            except Exception as e:
                                print(f"      ❌ Failed to click on Sub-product: {sub_product_name} - {e}")

                        driver.close()
                        driver.switch_to.window(driver.window_handles[1])
                        time.sleep(2)

            else:
                print(f"❌ No products found for {subcategory_name}.")

            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            time.sleep(2)

        driver.get("https://iwandw.com/products/")
        time.sleep(5)

except Exception as e:
    print(f"❌ Error encountered: {e}")

# Close WebDriver
driver.quit()

# Write links_data to CSV
csv_filename = 'links.csv'
with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=['Category', 'Subcategory', 'Product', 'Sub-product', 'Guide Type', 'Link', '3D Finish','Reference'])
    writer.writeheader()
    writer.writerows(links_data)

print(f"\n📊 Links have been saved to {csv_filename}")