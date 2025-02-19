# coding: utf-8
#!/usr/bin/env python

from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt 
import geopandas as gpd
import rasterio as rio
from rasterio.plot import show
import rasterio.mask
from zipfile import ZipFile
import os
from zipfile import ZipFile
from collections import OrderedDict

###_____CHANGE THESE FOR DIFFERENT TIME ZONES______###

start_date = 20210531
end_date = 20210605
name_of_file = "DC_from_satellite"

###___________must be after 2017-03-31_____________###

"""Comment below out to ignore input"""
print("Start date? #has to be recent!")
start_date = input()
print("End date?")
end_date = input()
print("What do you want to name the file?")
name_of_file = input()




# Log-In Credentials
user = 'thomaslan' 
password = 'ThisIsForResearch1234' 

api = SentinelAPI(user, password, 'https://scihub.copernicus.eu/dhus')

#Loads shapefile
DC_shape = gpd.read_file(r'/Users/thomaslanning/Desktop/Python_Practice/Satellites/Shapefiles/WashingtonDC.geojson')

#This Sentinel 2 tile is for DC (and baltimore)
tiles = ['18SUJ']

query_kwargs = { 'platformname': 'Sentinel-2', 'producttype': 'S2MSI1C', 'date': (str(start_date), str(end_date))}

products = OrderedDict()
for tile in tiles:
    kw = query_kwargs.copy()
    kw['tileid'] = tile  # products after 2017-03-31
    pp = api.query(**kw)
    products.update(pp)

#find which datapackets are available between the ^ time frame with that cloud coverage at that time frame
products_gdf = api.to_geodataframe(products)
products_gdf_sorted = products_gdf.sort_values(['cloudcoverpercentage'], ascending=[True])

print("Date of this image is:", products_gdf_sorted.beginposition[0])

api.download(products_gdf_sorted.index[0])

print("Finished Downloading. Will now make a cropped image.")

filepath = '{}.zip'.format(products_gdf_sorted.identifier[0])
with ZipFile(filepath, 'r') as zipObj:
    zipObj.extractall()
os.remove(filepath)

filepath = '{}.SAFE'.format(products_gdf_sorted.identifier[0])+'/GRANULE'
filepath += '/' + os.listdir(filepath)[0] + '/IMG_DATA/' 
filepath += sorted(os.listdir(filepath))[-1]
filepath

DC_map = rio.open(filepath)

#converts the home shapefile to the correct sattelite cooridante system: European Petrolium Surver Group 32632
DC_shape = DC_shape.to_crs(DC_map.crs)

# opens full image as source and then masks it with the (new) home shapefile
# also does this to the meta file and updates it accordingly
with rio.open(filepath) as src:
    out_image, out_transform = rio.mask.mask(src, DC_shape['geometry'], crop=True)
    out_meta = src.meta.copy()
    out_meta.update({"driver": "GTiff",
                 "height": out_image.shape[1],
                 "width": out_image.shape[2],
                 "transform": out_transform})
    
with rio.open("{}.tif".format(name_of_file), "w", **out_meta) as dest:
    dest.write(out_image)

# deletes the remaining folder    
import shutil
shutil.rmtree(products_gdf_sorted.identifier[0] + '.SAFE')

print("DONT FORGET TO EMPTY THE TRASH!")

